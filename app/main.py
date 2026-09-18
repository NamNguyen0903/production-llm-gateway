from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware.request_id import RequestIDMiddleware
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.db.session import close_database_connection


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await close_database_connection()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = settings or get_settings()

    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        debug=app_settings.debug,
        description=(
            "A production-oriented gateway that provides a unified API for multiple LLM providers."
        ),
        lifespan=lifespan,
    )

    application.state.settings = app_settings

    application.add_middleware(
        RequestIDMiddleware,
        header_name=app_settings.request_id_header,
    )

    register_exception_handlers(application)
    application.include_router(health_router)

    return application


app = create_app()
