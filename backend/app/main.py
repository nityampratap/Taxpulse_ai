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

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

