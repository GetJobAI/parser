from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.resumes import router as resumes_router
from app.config import get_settings
from app.db.client import Database
from app.db.repository import ResumeRepository
from app.events.publisher import ResumeParsedEventPublisher
from app.pipeline.resume_pipeline import ResumePipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.database = None
    app.state.resume_repository = None
    app.state.db_available = False
    app.state.resume_pipeline = ResumePipeline(parser_version=settings.parser_version)
    app.state.resume_event_publisher = ResumeParsedEventPublisher(
        rabbitmq_url=settings.rabbitmq_url,
        exchange_name=settings.rabbitmq_exchange,
        routing_key=settings.rabbitmq_routing_key,
        event_name=settings.rabbitmq_event_name,
        queue_name=settings.rabbitmq_queue,
    )

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

    if app.state.resume_event_publisher.enabled:
        try:
            await app.state.resume_event_publisher.connect()
        except Exception:
            logger.exception("RabbitMQ connection failed. Continuing without event publishing.")

    yield

    if app.state.resume_event_publisher is not None:
        await app.state.resume_event_publisher.close()
    if app.state.database is not None:
        await app.state.database.close()


app = FastAPI(
    title="Resume Parser Service",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(resumes_router)
