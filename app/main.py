from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.resumes import router as resumes_router
from app.config import get_settings
from app.db.client import Database
from app.db.repository import ResumeRepository
from app.pipeline.resume_pipeline import ResumePipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.database = None
    app.state.resume_repository = None
    app.state.db_available = False
    app.state.resume_pipeline = ResumePipeline(parser_version=settings.parser_version)

    if settings.database_url:
        database = Database(settings.database_url)
        try:
            await database.connect()
        except Exception:
            logger.exception("Database connection failed. Starting in docs-only mode.")
        else:
            app.state.database = database
            app.state.resume_repository = ResumeRepository(database.pool)
            app.state.db_available = True

    yield

    if app.state.database is not None:
        await app.state.database.close()


app = FastAPI(
    title="Resume Parser Service",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(resumes_router)
