from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str | None = None
    user_id_header: str = "X-User-Id"
    parser_version: str = "v1"
    rabbitmq_url: str | None = None
    rabbitmq_exchange: str = "resume.events"
    rabbitmq_routing_key: str = "resume.parsing.completed"
    rabbitmq_event_name: str = "resume.parsing.completed"
    rabbitmq_queue: str = "resume.parsing.completed.queue"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
