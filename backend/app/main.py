import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    SentinelException,
    ValidationException,
)
from app.core.logging import logger, setup_logging
from app.core.redis import redis_manager

# Configure structured logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SENTINEL — Git Governance, Merge Intelligence and Release Readiness Platform API",
    version="1.0.0",
)

# CORS configuration
# Allow localhost next.js in dev, otherwise configure appropriately
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1 import api_router

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_event():
    """Seed default administrator credentials if they do not exist."""
    from app.core.database import AsyncSessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.repositories.user_repo import user_repo

    async with AsyncSessionLocal() as db:
        admin = await user_repo.get_by_username(db, settings.ADMIN_USERNAME)
        if not admin:
            logger.info("Admin user not found in database. Seeding initial admin account...")
            try:
                new_admin = User(
                    username=settings.ADMIN_USERNAME,
                    email="admin@sentinel.local",
                    password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                    role="admin",
                    is_active=True,
                )
                db.add(new_admin)
                await db.commit()
                logger.info("Initial admin account seeded successfully.")
            except Exception as e:
                logger.error("Failed to seed initial admin account", error=str(e))
                await db.rollback()



# Global middleware to track request processing time
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.debug(
        "Request processed",
        path=request.url.path,
        method=request.method,
        duration=f"{process_time:.4f}s",
    )
    return response


# SentinelException Handlers
@app.exception_handler(SentinelException)
async def sentinel_exception_handler(request: Request, exc: SentinelException):
    # Determine HTTP status code based on exception type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, EntityNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, EntityAlreadyExistsException):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, ValidationException):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AuthenticationException):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, DatabaseException):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    logger.error(
        "Sentinel exception handled",
        code=exc.code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled generic exception",
        error=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
            }
        },
    )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """System health check endpoint.

    Verifies availability of PostgreSQL database and Redis cache/broker.
    Returns 200 if healthy, or 503 if any component is degraded.
    """
    db_healthy = False
    redis_healthy = False

    # Check Database connection
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_healthy = True
    except Exception as e:
        logger.error("Healthcheck database failure", error=str(e))

    # Check Redis connection
    try:
        redis_healthy = await redis_manager.ping()
    except Exception as e:
        logger.error("Healthcheck redis failure", error=str(e))

    status_code = (
        status.HTTP_200_OK
        if (db_healthy and redis_healthy)
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if status_code == status.HTTP_200_OK else "degraded",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "services": {
                "database": "online" if db_healthy else "offline",
                "redis": "online" if redis_healthy else "offline",
            },
        },
    )


@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "message": "Welcome to SENTINEL API. Refer to /docs for OpenAPI documentation.",
    }
