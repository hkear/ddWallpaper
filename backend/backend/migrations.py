import re
from sqlalchemy import inspect, text, Column, String, Boolean, Integer, DateTime, MetaData, Table
from sqlalchemy.exc import OperationalError

from backend.database import engine, Base
from backend.models import (
    User, VerificationCode, AuthConfig, WebhookConfig,
    StorageConfig, SmtpConfig, SmsConfig, Feedback, WallpaperDeviceType,
    DebugConfig, DebugLog, SiteConfig, WallpaperCategory,
)


def _table_exists(table_name: str) -> bool:
    return inspect(engine).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    cols = inspect(engine).get_columns(table_name)
    return any(c["name"] == column_name for c in cols)


def _column_is_nullable(table_name: str, column_name: str) -> bool:
    cols = inspect(engine).get_columns(table_name)
    for c in cols:
        if c["name"] == column_name:
            return c.get("nullable", True)
    return True


def run_migrations():
    """Run lightweight schema migrations for existing MySQL database."""
    print("🔧 Running schema migrations...")

    with engine.connect() as conn:
        # 1. users.email: fill nulls then make NOT NULL
        if _table_exists("users") and _column_exists("users", "email"):
            if _column_is_nullable("users", "email"):
                conn.execute(text("UPDATE users SET email = CONCAT('user_', id, '@placeholder.local') WHERE email IS NULL OR email = ''"))
                conn.execute(text("ALTER TABLE users MODIFY COLUMN email VARCHAR(100) NOT NULL"))
                conn.commit()
                print("✅ users.email set to NOT NULL")

        # 2. Add new user columns if missing
        new_user_cols = [
            ("phone", "ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL UNIQUE"),
            ("email_verified", "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE"),
            ("phone_verified", "ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE"),
            ("huawei_open_id", "ALTER TABLE users ADD COLUMN huawei_open_id VARCHAR(100) NULL UNIQUE"),
        ]
        for col, sql in new_user_cols:
            if _table_exists("users") and not _column_exists("users", col):
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Added users.{col}")
                except OperationalError as e:
                    print(f"⚠️ Skipped users.{col}: {e}")

        # 3. Create new tables
        Base.metadata.create_all(bind=engine, tables=[
            VerificationCode.__table__,
            AuthConfig.__table__,
            WebhookConfig.__table__,
            StorageConfig.__table__,
            SmtpConfig.__table__,
            SmsConfig.__table__,
            Feedback.__table__,
            DebugConfig.__table__,
            DebugLog.__table__,
        ])
        print("✅ New tables created if not exist")

        # 4. Add signed_url column to storage_config if missing
        if _table_exists("storage_config") and not _column_exists("storage_config", "signed_url"):
            try:
                conn.execute(text("ALTER TABLE storage_config ADD COLUMN signed_url BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("✅ Added storage_config.signed_url")
            except OperationalError as e:
                print(f"⚠️ Skipped storage_config.signed_url: {e}")

        # 5. Device type: single column → many-to-many junction table
        if _table_exists("wallpapers") and _column_exists("wallpapers", "device_type"):
            # Ensure junction table exists
            Base.metadata.create_all(bind=engine, tables=[WallpaperDeviceType.__table__])
            print("✅ wallpaper_device_types table ready")

            with engine.connect() as conn2:
                # Copy existing device_type values into junction table
                conn2.execute(text(
                    "INSERT INTO wallpaper_device_types (wallpaper_id, device_type) "
                    "SELECT id, device_type FROM wallpapers WHERE device_type IS NOT NULL"
                ))
                conn2.commit()
                print("✅ Moved device_type values to junction table")

                # Landscape wallpapers also get fold2 and fold3 types
                conn2.execute(text(
                    "INSERT IGNORE INTO wallpaper_device_types (wallpaper_id, device_type) "
                    "SELECT id, 'fold2' FROM wallpapers WHERE device_type = 'landscape'"
                ))
                conn2.commit()
                conn2.execute(text(
                    "INSERT IGNORE INTO wallpaper_device_types (wallpaper_id, device_type) "
                    "SELECT id, 'fold3' FROM wallpapers WHERE device_type = 'landscape'"
                ))
                conn2.commit()
                print("✅ Added fold2/fold3 for landscape wallpapers")

                # Drop old column
                conn2.execute(text("ALTER TABLE wallpapers DROP COLUMN device_type"))
                conn2.commit()
                print("✅ Dropped wallpapers.device_type column")

        # 6. SiteConfig singleton
        Base.metadata.create_all(bind=engine, tables=[SiteConfig.__table__])
        if _table_exists("site_config") and not _row_exists("site_config", 1):
            conn.execute(text("INSERT INTO site_config (id, upload_enabled) VALUES (1, TRUE)"))
            conn.commit()
            print("✅ Seeded site_config id=1")

        # 7. User avatar_url
        if _table_exists("users") and not _column_exists("users", "avatar_url"):
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500) NULL"))
            conn.commit()
            print("✅ Added users.avatar_url")

        # 8. Wallpaper categories many-to-many
        Base.metadata.create_all(bind=engine, tables=[WallpaperCategory.__table__])
        if _table_exists("wallpapers") and _column_exists("wallpapers", "category_id"):
            # Migrate historical single category values into junction table
            conn.execute(text(
                "INSERT IGNORE INTO wallpaper_categories (wallpaper_id, category_id) "
                "SELECT id, category_id FROM wallpapers WHERE category_id IS NOT NULL"
            ))
            conn.commit()
            print("✅ Migrated wallpapers.category_id to wallpaper_categories")

    print("🔧 Migrations completed.")


def _row_exists(table_name: str, row_id: int) -> bool:
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM {table_name} WHERE id = :rid"), {"rid": row_id})
            return result.fetchone() is not None
    except Exception:
        return False
