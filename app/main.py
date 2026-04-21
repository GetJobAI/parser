from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.resumes import router as resumes_router
from app.config import get_settings
from app.db.client import Database
from app.db.repository import ResumeRepository
from app.pipeline.resume_pipeline import ResumePipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    database = Database(settings.database_url)
    await database.connect()

    app.state.database = database
    app.state.resume_repository = ResumeRepository(database.pool)
    app.state.resume_pipeline = ResumePipeline(parser_version=settings.parser_version)

    yield

    await database.close()


app = FastAPI(
    title="Resume Parser Service",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(resumes_router)
