#!/usr/bin/env python3
"""Sync backend to both servers and rebuild Docker containers."""
import paramiko, os, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
SERVERS = [
    ("SERVER_IP_MAIN", "kay", "YOUR_SSH_PASSWORD"),
    ("SERVER_IP_SLAVE", "kay", "YOUR_SSH_PASSWORD"),
]
REMOTE = "/www/wwwroot/ddbz/backend"
FILES = [
    # backend package
    "backend/__init__.py",
    "backend/admin.py", "backend/admin_web.py",  # copies of routers/ versions (backward compat)
    "backend/auth.py", "backend/config.py", "backend/database.py",
    "backend/email.py", "backend/huawei_oauth.py", "backend/main.py",
    "backend/migrations.py", "backend/models.py", "backend/schemas.py",
    "backend/sms.py", "backend/storage.py", "backend/verification.py",
    "backend/webhook.py", "backend/favicon_64.png",
    # routers
    "backend/routers/__init__.py",
    "backend/routers/admin.py", "backend/routers/admin_web.py",
    "backend/routers/categories.py", "backend/routers/favorites.py",
    "backend/routers/feedback.py", "backend/routers/users.py",
    "backend/routers/wallpapers.py",
    # backend scripts
    "backend/scripts/__init__.py",
    "backend/scripts/regenerate_urls.py", "backend/scripts/wallpapers.py",
    # ops scripts / website
    "scripts/backup_db.sh", "scripts/restore_db.sh", "scripts/migrate_to_oss.py",
    "../website/feedback.php",
    # build & deploy
    "Dockerfile", "docker-compose.yml", "requirements.txt",
    "ai_tag_wallpapers.py",
]

def _safe_print(text):
    """Print text safely on Windows consoles with limited code pages."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: encode with replacement for the current stdout encoding
        encoded = text.encode(sys.stdout.encoding or "utf-8", errors="replace")
        sys.stdout.buffer.write(encoded + b"\n")
        sys.stdout.flush()


def deploy(host, user, pwd):
    print(f"\n{'='*50}\n  {host}\n{'='*50}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=pwd, timeout=15)
        sftp = ssh.open_sftp()

        for rel in FILES:
            lp = os.path.join(BASE, rel)
            if not os.path.exists(lp): continue
            rp = f"{REMOTE}/{rel}"
            try: sftp.stat(os.path.dirname(rp))
            except: ssh.exec_command(f"mkdir -p {os.path.dirname(rp)}")
            sftp.put(lp, rp)

        # Also copy routers/admin.py → backend/admin.py for backward compat (both copies exist in container)
        sftp.put(os.path.join(BASE, "backend/routers/admin.py"), f"{REMOTE}/backend/admin.py")
        sftp.put(os.path.join(BASE, "backend/routers/admin_web.py"), f"{REMOTE}/backend/admin_web.py")
        sftp.close()
        _safe_print("  Files synced.")

        # Rebuild Docker
        _safe_print("  Rebuilding...")
        cmd = f"cd {REMOTE} && sudo docker-compose down && sudo docker-compose build --no-cache && sudo docker-compose up -d"
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300, get_pty=True)
        out_lines = []
        for line in iter(stdout.readline, ""):
            t = line.rstrip()
            if t and any(k in t for k in ["Built", "Created", "Started", "Healthy", "ERROR", "FAIL"]):
                out_lines.append(t[:120])
        for l in out_lines[-8:]: _safe_print(f"  {l}")
        rc = stdout.channel.recv_exit_status()
        if rc == 0:
            time.sleep(2)
            _, out, _ = ssh.exec_command("curl -s http://localhost:8082/", timeout=5)
            _safe_print(f"  OK - {out.read().decode().strip()[:60]}")
        else:
            _safe_print(f"  FAIL (rc={rc})")
        ssh.close()
        return rc == 0
    except Exception as e:
        _safe_print(f"  ERROR: {e}")
        return False

if __name__ == "__main__":
    ok = all(deploy(h, u, p) for h, u, p in SERVERS)
    print(f"\n{'='*50}\n  {'ALL OK' if ok else 'SOME FAILED'}\n{'='*50}")
    sys.exit(0 if ok else 1)
