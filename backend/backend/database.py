import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from backend.config import get_settings

settings = get_settings()

# Use check_same_thread=False for SQLite compat, not needed for MySQL
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables, run migrations, then insert default data if needed."""
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Run lightweight migrations for existing databases
    from backend.migrations import run_migrations
    run_migrations()

    db = SessionLocal()
    try:
        # Seed default categories if empty
        from backend.models import Category
        if db.query(Category).count() == 0:
            defaults = [
                Category(name="简约", slug="minimal", icon="⚪", sort=1),
                Category(name="风景", slug="landscape", icon="🏞️", sort=2),
                Category(name="动漫", slug="anime", icon="🎨", sort=3),
                Category(name="科技", slug="tech", icon="🤖", sort=4),
                Category(name="国风", slug="chinese", icon="🏯", sort=5),
                Category(name="少女", slug="girl", icon="🌸", sort=6),
                Category(name="星空", slug="starry", icon="🌌", sort=7),
                Category(name="城市", slug="city", icon="🌆", sort=8),
            ]
            db.add_all(defaults)
            db.commit()
            print("✅ Default categories seeded.")

        # Seed default admin user if not exists
        from backend.models import User
        from backend.auth import hash_password
        if db.query(User).filter(User.username == "admin").count() == 0:
            admin_pwd = os.environ.get("ADMIN_PASSWORD", "admin123")
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
            db.add(User(
                username="admin",
                email=admin_email,
                hashed_password=hash_password(admin_pwd),
                is_admin=True,
            ))
            db.commit()
            print(f"✅ Default admin user seeded (admin / {'*'*len(admin_pwd)}).")

        # Seed default auth config if empty
        from backend.models import AuthConfig
        if db.query(AuthConfig).count() == 0:
            from backend.config import get_settings
            s = get_settings()
            db.add(AuthConfig(
                id=1,
                enable_email_verify=s.REGISTER_ENABLE_EMAIL_VERIFY,
                enable_sms_verify=s.REGISTER_ENABLE_SMS_VERIFY,
                require_email=s.REGISTER_REQUIRE_EMAIL,
                email_provider="smtp",
                sms_provider=s.SMS_PROVIDER,
                enable_huawei_login=False,
            ))
            db.commit()
            print("✅ Default auth config seeded.")

        # Seed default webhook config if empty
        from backend.models import WebhookConfig
        if db.query(WebhookConfig).count() == 0:
            default_url = settings.WEBHOOK_URL or "YOUR_UNIPUSH_WEBHOOK_URL"
            db.add(WebhookConfig(id=1, url=default_url))
            db.commit()
            print("✅ Default webhook config seeded.")

        # Seed default debug config if empty
        from backend.models import DebugConfig
        if db.query(DebugConfig).count() == 0:
            db.add(DebugConfig(id=1, enabled=False, log_retention_days=7))
            db.commit()
            print("✅ Default debug config seeded.")
    except Exception as e:
        print(f"⚠️  Seed error (non-fatal): {e}")
        db.rollback()
    finally:
        db.close()
