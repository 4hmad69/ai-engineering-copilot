from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api import (
    chat,
    documentation,
    documents,
    evaluation,
    health,
    planner,
    projects,
    review,
    search,
    upload,
)
from backend.app.config import get_settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import configure_logging
from backend.app.db.session import close_database_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_database_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.api_prefix, tags=["Health"])
    app.include_router(upload.router, prefix=settings.api_prefix, tags=["Upload"])
    app.include_router(projects.router, prefix=settings.api_prefix, tags=["Projects"])
    app.include_router(documents.router, prefix=settings.api_prefix, tags=["Documents"])
    app.include_router(search.router, prefix=settings.api_prefix, tags=["Search"])
    app.include_router(chat.router, prefix=settings.api_prefix, tags=["Chat"])
    app.include_router(review.router, prefix=settings.api_prefix, tags=["Review"])
    app.include_router(planner.router, prefix=settings.api_prefix, tags=["Planner"])
    app.include_router(
        documentation.router,
        prefix=settings.api_prefix,
        tags=["Documentation"],
    )
    app.include_router(evaluation.router, prefix=settings.api_prefix, tags=["Evaluation"])

    return app


app = create_app()