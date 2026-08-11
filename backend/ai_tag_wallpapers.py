#!/usr/bin/env python3
"""
AI 壁纸信息更新脚本
使用 Qwen3-VL-Flash 分析壁纸图片，自动生成标题、描述、标签、分类并更新数据库。

用法：
  # 容器外运行（需要宿主机能连 MySQL 3306 端口）
  python ai_tag_wallpapers.py

  # 容器内运行
  python ai_tag_wallpapers.py --inside-docker

  # 只分析前 N 张（测试用）
  python ai_tag_wallpapers.py --limit 5

  # 跳过已有完善信息的壁纸（默认行为）
  python ai_tag_wallpapers.py --skip-tagged

  # 强制全部重新分析
  python ai_tag_wallpapers.py --force-all

配置：在同目录下创建 ai_config.json，内容：
{
  "api_key": "YOUR_DASHSCOPE_API_KEY",
  "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
  "model": "qwen3-vl-flash",
  "db_host": "localhost",
  "db_port": 3306,
  "db_user": "wallpaper",
  "db_password": "YOUR_DB_PASSWORD",
  "db_name": "wallpaper_db",
  "request_delay": 1.5,
  "max_tokens": 300
}

依赖：Python 3.8+，无第三方库（仅用标准库）
"""

import json
import time
import sys
import os
import subprocess
import urllib.request
import urllib.error
import argparse
import base64
from datetime import datetime

# ─── 配置 ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "ai_config.json")
# 日志优先写脚本目录，无权限则写 /tmp
try:
    _test = os.path.join(SCRIPT_DIR, ".log_test")
    with open(_test, "w") as f: f.write("")
    os.remove(_test)
    LOG_PATH = os.path.join(SCRIPT_DIR, "ai_tag_wallpapers.log")
except (PermissionError, OSError):
    LOG_PATH = "/tmp/ai_tag_wallpapers.log"

DEFAULT_CONFIG = {
    "api_key": "YOUR_DASHSCOPE_API_KEY",
    "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "model": "qwen3-vl-flash",
    "db_host": "localhost",
    "db_port": 3306,
    "db_user": "wallpaper",
    "db_password": "YOUR_DB_PASSWORD",
    "db_name": "wallpaper_db",
    "request_delay": 1.5,
    "max_tokens": 300,
    "webhook_url": "",
}

# 数据库分类映射
CATEGORIES = {
    1:  "简约丨minimal",
    2:  "风景丨landscape",
    3:  "动漫丨anime",
    4:  "科技丨tech",
    5:  "中国风丨chinese",
    6:  "美女丨girl",
    7:  "星空丨starry",
    8:  "城市丨city",
    11: "动物丨animal",
    12: "美食丨food",
    13: "汽车丨car",
    14: "游戏丨game",
    15: "抽象丨abstract",
    16: "自然丨nature",
}

# 用于告诉 AI 的分类选项文本
CATEGORY_OPTIONS = "\n".join(
    f"  {cid} - {desc}" for cid, desc in CATEGORIES.items()
)

SYSTEM_PROMPT = f"""你是一个壁纸内容分析专家。请根据提供的壁纸图片，用中文输出以下信息。

## 输出格式（严格 JSON）
{{
  "title": "壁纸标题（10字以内，抓住画面核心特征，有吸引力）",
  "description": "壁纸描述（30字以内，描述画面内容或风格）",
  "tags": "标签1,标签2,标签3（英文逗号分隔，不超过5个标签，每个标签2-6字）",
  "category_id": 分类ID数字
}}

## 分类选项
{CATEGORY_OPTIONS}

## 规则
1. title：必须有意义，不能是 uuid、随机字符串。如果画面有明显主体，以主体命名。
2. description：描述画面场景/风格/色调，控制在30字内。
3. tags：选择最能描述画面的2-5个中文标签，用英文逗号分隔。
4. category_id：从上面的分类选项中选一个最匹配的数字ID。
5. 只输出 JSON，不要有任何其他文字。
"""


def load_config() -> dict:
    """加载配置：优先读 ai_config.json，不存在则用默认值"""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 用默认值补全缺失字段
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
        return cfg
    return dict(DEFAULT_CONFIG)


def log(msg: str, level: str = "INFO"):
    """写日志到文件+控制台"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─── 数据库操作 ────────────────────────────────────────────────────────────────

def get_mysql_cmd(cfg: dict, inside_docker: bool = False) -> list[str]:
    """构建 mysql CLI 命令"""
    if inside_docker:
        host = "mysql"
    else:
        host = cfg["db_host"]
    return [
        "mysql",
        "-h", host,
        "-P", str(cfg["db_port"]),
        "-u", cfg["db_user"],
        f"-p{cfg['db_password']}",
        "-D", cfg["db_name"],
        "--default-character-set=utf8mb4",
        "--batch",
        "--skip-column-names",
    ]


def _mysql_exec(cfg: dict, sql: str) -> str:
    """执行 SQL 并返回 stdout。
    优先用 sudo docker exec（宿主机），否则直接 mysql CLI（容器内或纯 MySQL 环境）。
    """
    # 尝试用 sudo docker exec
    docker_cmd = [
        "sudo", "docker", "exec", "wallpaper_mysql",
        "mysql",
        "-u", cfg["db_user"],
        f"-p{cfg['db_password']}",
        "-D", cfg["db_name"],
        "--default-character-set=utf8mb4",
        "--batch",
        "--skip-column-names",
        "-e", sql,
    ]
    try:
        r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return r.stdout.strip()
        # docker exec 失败，尝试直接连
        if r.stderr and "permission denied" not in r.stderr.lower():
            raise RuntimeError(r.stderr.strip())
    except FileNotFoundError:
        pass  # sudo 或 docker 不存在

    # 回退：直接 mysql CLI
    return _mysql_exec_direct(cfg, sql)


def _mysql_exec_direct(cfg: dict, sql: str) -> str:
    """直接通过 mysql CLI 连接（容器内或 --protocol=TCP 宿主机）"""
    cmd = [
        "mysql",
        "-h", cfg.get("db_host", "localhost"),
        "-P", str(cfg.get("db_port", 3306)),
        "--protocol=TCP",
        "-u", cfg["db_user"],
        f"-p{cfg['db_password']}",
        "-D", cfg["db_name"],
        "--default-character-set=utf8mb4",
        "--batch",
        "--skip-column-names",
        "-e", sql,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0 and r.stderr:
            err = r.stderr.strip()
            if "Warning" not in err and "Using a password" not in err:
                raise RuntimeError(err)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("MySQL timeout")


def get_wallpapers_to_update(cfg: dict, limit: int = 0, skip_tagged: bool = True) -> list[dict]:
    """获取需要更新的壁纸列表"""
    conditions = []
    if skip_tagged:
        conditions.append(
            "(description IS NULL OR description = '' OR description LIKE '暂无%' "
            "OR tags IS NULL OR JSON_LENGTH(tags) = 0 "
            "OR title = CONCAT('壁纸-', SUBSTRING(original_url, -20)) "
            "OR (CHAR_LENGTH(title) > 20 AND title NOT LIKE '% %'))"
        )
    conditions.append("original_url IS NOT NULL AND original_url != ''")

    where = " AND ".join(conditions)
    limit_clause = f" LIMIT {limit}" if limit > 0 else ""

    sql = f"""
    SELECT id, title, original_url, category_id
    FROM wallpapers
    WHERE {where}
    ORDER BY id ASC
    {limit_clause}
    """
    output = _mysql_exec(cfg, sql)
    if not output:
        return []

    rows = []
    for line in output.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 4:
            rows.append({
                "id": int(parts[0]),
                "title": parts[1],
                "url": parts[2],
                "category_id": int(parts[3]) if parts[3] and parts[3] != "NULL" else None,
            })
    return rows


def update_wallpaper_metadata(cfg: dict, wp_id: int, title: str, description: str, tags: str,
                               category_id: int):
    """更新壁纸元数据"""
    # Escape single quotes for SQL
    t = title.replace("'", "\\'")
    d = description.replace("'", "\\'")

    # 处理 tags：存储为 JSON 数组
    tag_list = [tag.strip().replace("'", "\\'") for tag in tags.split(",") if tag.strip()]
    tags_json = json.dumps(tag_list, ensure_ascii=False)

    sql = f"""
    UPDATE wallpapers SET title='{t}', description='{d}', tags='{tags_json}'
    WHERE id={wp_id}
    """
    _mysql_exec(cfg, sql)

    # 更新分类关联表
    if category_id and category_id in CATEGORIES:
        check_sql = f"SELECT COUNT(*) FROM wallpaper_categories WHERE wallpaper_id={wp_id} AND category_id={category_id}"
        count = _mysql_exec(cfg, check_sql)
        if not count or count.strip() == "0":
            del_sql = f"DELETE FROM wallpaper_categories WHERE wallpaper_id={wp_id}"
            _mysql_exec(cfg, del_sql)
            ins_sql = f"INSERT INTO wallpaper_categories (wallpaper_id, category_id) VALUES ({wp_id}, {category_id})"
            _mysql_exec(cfg, ins_sql)

    # 同时更新 wallpapers.category_id（向后兼容）
    if category_id:
        cat_sql = f"UPDATE wallpapers SET category_id={category_id} WHERE id={wp_id}"
        _mysql_exec(cfg, cat_sql)


# ─── AI API 调用 ──────────────────────────────────────────────────────────────

def download_image_to_base64(url: str, max_size_mb: float = 4.0) -> str | None:
    """下载图片并转为 base64 data URI"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "iWallpaper-AITagger/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) > max_size_mb * 1024 * 1024:
                log(f"  图片过大 ({len(data) / 1024 / 1024:.1f}MB)，跳过", "WARN")
                return None
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception as e:
        log(f"  下载图片失败: {e}", "WARN")
        return None


def analyze_wallpaper(cfg: dict, image_url: str) -> dict | None:
    """调用 Qwen3-VL-Flash 分析壁纸。
    直接把 OSS 签名 URL 传给 Qwen，服务器不下载图片，零带宽消耗。
    """
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张壁纸图片"},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": cfg["max_tokens"],
        "temperature": 0.3,
    }

    req = urllib.request.Request(
        cfg["api_url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        err_msg = err_body[:300]
        log(f"  API HTTP {e.code}: {err_msg}", "ERROR")
        # 判断是否是图片不可访问（URL 过期等）
        if "image" in err_msg.lower() and ("invalid" in err_msg.lower() or "not found" in err_msg.lower()):
            log(f"  → 可能是 OSS URL 已过期，需先运行 regenerate_urls.py 刷新", "WARN")
        return None
    except Exception as e:
        log(f"  API 调用失败: {e}", "ERROR")
        return None

    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        log(f"  API 返回空内容", "WARN")
        return None

    # 提取 JSON（可能被 markdown 代码块包裹）
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if len(lines) > 2 else content

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取 {} 内容
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                result = json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                log(f"  JSON 解析失败: {content[:200]}", "WARN")
                return None
        else:
            log(f"  JSON 解析失败: {content[:200]}", "WARN")
            return None

    return result


# ─── Webhook ───────────────────────────────────────────────────────────────────

def send_webhook(cfg: dict, msg: str):
    """发送 Webhook 通知（企业微信格式）"""
    url = cfg.get("webhook_url", "")
    if not url:
        return
    payload = json.dumps({
        "msgtype": "text",
        "text": {"content": msg}
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log(f"Webhook 发送失败: {e}", "WARN")


# ─── 主流程 ────────────────────────────────────────────────────────────────────

def validate_result(result: dict) -> dict | None:
    """校验并规范化 AI 返回结果"""
    title = str(result.get("title", "")).strip()
    description = str(result.get("description", "")).strip()
    tags = str(result.get("tags", "")).strip()

    if not title:
        return None

    # 限制长度（中文按字数）
    if len(title) > 30:
        title = title[:30]
    if len(description) > 30:
        description = description[:30]
    if len(tags) > 20:
        # 截断到20字内
        while len(tags) > 20:
            parts = tags.split(",")
            if len(parts) > 1:
                tags = ",".join(parts[:-1])
            else:
                tags = tags[:20]
                break

    # 中文逗号转英文
    tags = tags.replace("，", ",").replace("、", ",")
    # 过滤空标签
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    tags = ",".join(tag_list[:5])  # 最多5个标签

    category_id = result.get("category_id")
    if category_id is not None:
        try:
            category_id = int(category_id)
        except (ValueError, TypeError):
            category_id = None
    if category_id not in CATEGORIES:
        category_id = None

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "category_id": category_id,
    }


def main():
    parser = argparse.ArgumentParser(description="AI 壁纸信息更新脚本")
    parser.add_argument("--inside-docker", action="store_true", help="在 Docker 容器内运行")
    parser.add_argument("--limit", type=int, default=0, help="最多处理 N 张（0=全部）")
    parser.add_argument("--skip-tagged", action="store_true", default=True, help="跳过已有信息的壁纸（默认）")
    parser.add_argument("--force-all", action="store_true", help="强制重新分析所有壁纸")
    parser.add_argument("--dry-run", action="store_true", help="仅列出要处理的壁纸，不实际更新")
    args = parser.parse_args()

    if args.force_all:
        args.skip_tagged = False

    cfg = load_config()

    log("=" * 60)
    log("AI 壁纸信息更新脚本 启动")
    log(f"模式: {'容器内' if args.inside_docker else '宿主机'}")
    log(f"限制: {args.limit if args.limit > 0 else '全部'}")
    log(f"跳过已标记: {args.skip_tagged}")
    log(f"预期执行: {'是' if not args.dry_run else '否（dry-run）'}")
    log(f"模型: {cfg['model']}")

    # 获取待处理壁纸
    wallpapers = get_wallpapers_to_update(
        cfg, limit=args.limit, skip_tagged=args.skip_tagged
    )
    log(f"待处理壁纸: {len(wallpapers)} 张")

    if args.dry_run:
        for wp in wallpapers[:20]:
            print(f"  #{wp['id']} | {wp['title'][:30]}")
        if len(wallpapers) > 20:
            print(f"  ... 及其他 {len(wallpapers) - 20} 张")
        return

    success = 0
    fail = 0
    skip = 0

    for i, wp in enumerate(wallpapers):
        wp_id = wp["id"]
        log(f"[{i + 1}/{len(wallpapers)}] 处理壁纸 #{wp_id}: {wp['title'][:40]}")

        # 调用 AI 分析
        result = analyze_wallpaper(cfg, wp["url"])
        if result is None:
            log(f"  ✗ AI 分析失败，跳过", "WARN")
            fail += 1
            continue

        # 校验结果
        validated = validate_result(result)
        if validated is None:
            log(f"  ✗ 结果校验失败：{json.dumps(result, ensure_ascii=False)[:200]}", "WARN")
            fail += 1
            continue

        # 输出结果
        log(f"  标题: {validated['title']}")
        log(f"  描述: {validated['description']}")
        log(f"  标签: {validated['tags']}")
        log(f"  分类ID: {validated['category_id']} -> {CATEGORIES.get(validated['category_id'], 'N/A')}")

        # 更新数据库
        try:
            update_wallpaper_metadata(
                cfg, wp_id,
                validated["title"],
                validated["description"],
                validated["tags"],
                validated["category_id"]
            )
            log(f"  ✓ 已更新", "SUCCESS")
            success += 1
        except Exception as e:
            log(f"  ✗ 数据库更新失败: {e}", "ERROR")
            fail += 1

        # 限速
        time.sleep(cfg.get("request_delay", 1.5))

    log("=" * 60)
    summary = f"AI 壁纸信息更新完成: 成功 {success}, 失败 {fail}, 跳过 {skip}, 总计 {len(wallpapers)}"
    log(summary)
    log("=" * 60)

    # Webhook 通知
    if success > 0 or fail > 0:
        hook_msg = f"【AI 壁纸标签更新】\n服务器: {os.uname().nodename if hasattr(os, 'uname') else 'unknown'}\n结果: 成功 {success}, 失败 {fail}, 跳过 {skip}, 总计 {len(wallpapers)}\n日志: /tmp/ai_tag_wallpapers.log"
        send_webhook(cfg, hook_msg)


if __name__ == "__main__":
    main()
