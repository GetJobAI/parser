from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aio_pika

logger = logging.getLogger(__name__)


class ResumeParsedEventPublisher:
    def __init__(
        self,
        *,
        rabbitmq_url: str | None,
        exchange_name: str,
        routing_key: str,
        event_name: str,
        queue_name: str,
    ) -> None:
        self._rabbitmq_url = rabbitmq_url
        self._exchange_name = exchange_name
        self._routing_key = routing_key
        self._event_name = event_name
        self._queue_name = queue_name
        self._connection: Any | None = None
        self._channel: Any | None = None
        self._exchange: Any | None = None
        self._queue: Any | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._rabbitmq_url)

    async def connect(self) -> None:
        if not self._rabbitmq_url:
            return

        import aio_pika

        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        self._queue = await self._channel.declare_queue(self._queue_name, durable=True)
        await self._queue.bind(self._exchange, routing_key=self._routing_key)

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        if self._connection is not None and not self._connection.is_closed:
            await self._connection.close()

    async def publish_resume_parsed(
        self,
        *,
        resume_id: str,
        user_id: str,
    ) -> bool:
        if not self.enabled:
            return False
        if self._exchange is None:
            logger.warning("RabbitMQ exchange is not initialized. Resume parsed event was not published.")
            return False

        import aio_pika

        body = self.build_payload(resume_id=resume_id, user_id=user_id)
        message = aio_pika.Message(
            body=json.dumps(body).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            type=self._event_name,
        )

        await self._exchange.publish(message, routing_key=self._routing_key)
        return True

    def build_payload(self, *, resume_id: str, user_id: str) -> dict[str, str]:
        return {
            "resume_id": resume_id,
            "user_id": user_id,
        }
