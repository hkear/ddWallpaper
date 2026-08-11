import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from jose import jwt, JWTError

from backend.config import get_settings
from backend.database import init_db, SessionLocal
from backend.routers import users, wallpapers, favorites, categories, feedback, admin as admin_api
from backend.routers.admin_web import router as admin_web_router
from backend.routers.wallpapers import cleanup_stale_pending

settings = get_settings()


async def _periodic_cleanup(interval_seconds: int = 3600):
    """Background task to delete pending wallpapers older than 24 hours."""
    while True:
        await asyncio.sleep(interval_seconds)
        db = SessionLocal()
        try:
            count = cleanup_stale_pending(db)
            if count:
                print(f"🧹 Cleaned up {count} stale pending wallpaper(s)")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting iWallpaper API...")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    init_db()
    print("✅ Database initialized.")

    # Ensure admin (id=1) password is reset if still default
    db = SessionLocal()
    try:
        from backend.models import User
        from backend.auth import hash_password
        admin = db.query(User).filter(User.id == 1).first()
        if admin:
            admin.hashed_password = hash_password("YOUR_ADMIN_PASSWORD")
            db.commit()
            print("🔑 Admin password enforced to default.")
    except Exception as e:
        print(f"⚠️ Admin password check error: {e}")
    finally:
        db.close()

    # Run one cleanup at startup
    db = SessionLocal()
    try:
        count = cleanup_stale_pending(db)
        if count:
            print(f"🧹 Cleaned up {count} stale pending wallpaper(s) at startup")
    except Exception as e:
        print(f"⚠️ Startup cleanup error: {e}")
    finally:
        db.close()

    # Start periodic cleanup task
    task = asyncio.create_task(_periodic_cleanup())
    yield
    task.cancel()
    print("👋 Shutting down iWallpaper API...")


_docs_enabled = True  # Always enable; protected by AdminDocsMiddleware below

app = FastAPI(
    title="多点壁纸 API",
    version="1.2.0",
    description="HarmonyOS 壁纸平台后端 API",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)


class AdminDocsMiddleware(BaseHTTPMiddleware):
    """Protect /docs, /redoc, /openapi.json — admin-only, app API unaffected."""

    DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.rstrip("/")

        # Only protect docs paths
        if not any(path == p or path.startswith(p) for p in self.DOCS_PATHS):
            return await call_next(request)

        # Check token from cookie or Authorization header
        token = request.cookies.get("admin_token")
        if not token:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]

        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                if payload.get("is_admin"):
                    return await call_next(request)
            except JWTError:
                pass

        # Return 403 HTML for browser, JSON for API calls
        if "text/html" in request.headers.get("Accept", ""):
            return Response(
                content=FORBIDDEN_HTML,
                status_code=403,
                media_type="text/html",
            )
        return JSONResponse(
            status_code=403,
            content={"detail": "Admin access required. Login at /admin/login first."},
        )


FORBIDDEN_HTML = """<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><title>403 - 需要管理员权限</title>
<style>body{font-family:sans-serif;background:#0f0f23;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.box{text-align:center;background:#16162a;padding:40px 60px;border-radius:16px}
h1{color:#ff4757;font-size:48px;margin:0}h2{margin:8px 0 24px;color:#888}
a{color:#ff6b6b;text-decoration:none;font-size:14px}a:hover{text-decoration:underline}</style></head>
<body><div class="box"><h1>403</h1><h2>需要管理员权限</h2><p>请先 <a href="/admin/login">登录管理后台</a></p></div></body></html>"""


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


# Security middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AdminDocsMiddleware)  # Protect docs behind admin auth
if not settings.DEBUG_MODE:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.ddbz.cn", "ddbz.cn", "www.ddbz.cn", "localhost", "127.0.0.1"],
    )

# CORS
_cors_origins = ["*"] if settings.DEBUG_MODE else settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (serve uploaded images)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Routes
app.include_router(users.router, prefix="/api/v1")
app.include_router(wallpapers.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(admin_api.router, prefix="/api/v1")
app.include_router(admin_web_router)


@app.get("/")
def root():
    return {"name": "多点壁纸 API", "version": "1.2.0", "status": "ok"}


if settings.DEBUG_MODE or settings.ENABLE_HEALTH_CHECK:
    @app.get("/health")
    def health():
        return {"status": "healthy"}
