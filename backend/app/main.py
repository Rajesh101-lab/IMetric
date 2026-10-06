import os
import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.db.session import AsyncSessionLocal, engine
from app.db.migrations import upgrade_database
from app.services.auth import seed_initial_user_if_empty
from app.services.pages import recover_stuck_pending_pages
from app.services.refresh_jobs import prune_refresh_history, refresh_worker
from app.api.v1 import auth, pages, health, config as config_api, campaigns


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)
        process_time = time.time() - start_time

        # Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "frame-ancestors 'none';"
        )
        if settings.ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        response.headers["X-Request-ID"] = request_id
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
            extra={"request_id": request_id, "client_ip": request.client.host if request.client else None}
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    async with engine.begin() as conn:
        await conn.run_sync(upgrade_database)

    async with AsyncSessionLocal() as db:
        await seed_initial_user_if_empty(db)
        await prune_refresh_history(db)

    # Recover stuck pending pages on startup
    await recover_stuck_pending_pages()

    worker_task = None
    if os.environ.get("RUN_WORKER", "true").lower() == "true":
        stop_worker = asyncio.Event()
        worker_task = asyncio.create_task(refresh_worker(stop_worker))
    else:
        stop_worker = None

    yield
    # Shutdown actions
    if worker_task:
        stop_worker.set()
        await worker_task
    await engine.dispose()


is_prod = (settings.ENV == "production")

app = FastAPI(
    title="IMetric API",
    version="1.0.0",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
    lifespan=lifespan,
)

# Custom Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Strict CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://i-metric-[a-zA-Z0-9-]+-im-etric\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization", "Cookie"],
)

# DEBUG: Print FULL DB URL to show what Render sees in the logs
logger.info(f"STARTUP DB URL FOUND: {settings.DATABASE_URL}")

# Standardized Exception Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        err_body = exc.detail
    else:
        err_body = {
            "code": "HTTP_ERROR",
            "message": str(exc.detail) if isinstance(exc.detail, str) else "An HTTP error occurred."
        }
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": err_body}
    )

# DEBUG: Print masked DB URL to show what Render sees in the logs
logger.info(f"STARTUP DB URL MASKED: {settings.DATABASE_URL[:30]}...")

@app.exception_handler(Exception)
async def global_uncaught_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Uncaught exception (request_id={request_id}): {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later."
            }
        }
    )


# Mount API routes under /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(pages.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(config_api.router, prefix="/api/v1")

# Static files & Single Page Application (SPA) fallback from frontend/dist
frontend_dist_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)

if os.path.exists(frontend_dist_path):
    assets_path = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "API endpoint not found."})
        file_target = os.path.join(frontend_dist_path, full_path)
        if os.path.exists(file_target) and os.path.isfile(file_target):
            return FileResponse(file_target)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
