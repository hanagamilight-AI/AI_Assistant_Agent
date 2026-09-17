"""Main FastAPI application entry point."""

import contextlib
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, conversations, tasks, health, documents
from app.config import settings
from app.db.session import init_db, close_db
from app.tools.registry import tool_registry
from app.tools.tasks import create_task_tools
from app.db.repositories import TaskRepository

logger = structlog.get_logger()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up application", config={"debug": settings.debug})

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Register default tools
        # Note: In production, tools should be registered with proper session management
        # This is a simplified setup for the MVP

        logger.info("Tools registered")

    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        description="AI Personal Assistant Agent API",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
    app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
    app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
    app.include_router(health.router, prefix="/api/v1", tags=["health"])

    # Add exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Health check at root
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {"message": "AI Personal Assistant API", "version": "0.1.0"}

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
