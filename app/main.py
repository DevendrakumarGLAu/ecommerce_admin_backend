"""FastAPI application entrypoint: wiring, middleware, routers, and lifecycle."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, cart, categories, products, settings as settings_router, uploads, users, wishlist
from app.core.config import settings
from app.core.database import engine
from app.core.logging import configure_logging, get_logger
from app.core.redis import close_redis
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.schemas.common import SuccessResponse

logger = get_logger("app.lifecycle")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    logger.info("Application startup complete")
    yield
    await close_redis()
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready REST API backend for an e-commerce product catalog.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(cart.router, prefix=settings.API_V1_PREFIX)
app.include_router(wishlist.router, prefix=settings.API_V1_PREFIX)
app.include_router(uploads.router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)


@app.get(
    "/health",
    response_model=SuccessResponse[dict],
    tags=["Health"],
    summary="Health check",
    description="Lightweight liveness probe used by load balancers and uptime monitors.",
)
async def health_check() -> SuccessResponse[dict]:
    return SuccessResponse(message="Service is healthy", data={"status": "ok"})
