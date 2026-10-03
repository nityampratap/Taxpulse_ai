from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.errors.handlers import register_error_handlers
from app.middleware.request_id import RequestIdMiddleware
from app.api.v1.api import api_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.demo import router as demo_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Tax Reconciliation & Compliance Intelligence API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 1. Request ID and secret-safe logging middleware
app.add_middleware(RequestIdMiddleware)

# 2. CORS configuration strictly restricted to configured frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# 3. Standard consistent error handlers
register_error_handlers(app)

# 4. Root /api/health and /api/demo endpoints
app.include_router(health_router, prefix="/api")
app.include_router(demo_router, prefix="/api")

# 5. Full v1 API specification endpoints
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# 6. Serve static frontend SPA if directory exists
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Never intercept API routes — let them 404 naturally
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "NOT_FOUND", "message": f"/{full_path} not found", "details": None}},
            )
        # Serve exact file if it exists (e.g. favicon.svg, icons.svg)
        if full_path:
            file_path = static_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)
        # Fallback to SPA index.html for all client-side routes
        return FileResponse(static_dir / "index.html")

