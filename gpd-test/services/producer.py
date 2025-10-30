from __future__ import annotations

import json
import ssl
from typing import Any

import certifi
from aiokafka import AIOKafkaProducer
from core.config import settings
from services.keyvault import get_eventhub_connection_string


class ProducerService:
    """Thin wrapper around aiokafka producer to manage lifecycle and JSON sends."""

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        connection_string = get_eventhub_connection_string()
        namespace = settings.eventhub_namespace

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        if hasattr(ssl, 'TLSVersion'):
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

        self._producer = AIOKafkaProducer(
            bootstrap_servers=f"{namespace}.servicebus.windows.net:9093",
            security_protocol='SASL_SSL',
            sasl_mechanism='PLAIN',
            sasl_plain_username='$ConnectionString',
            sasl_plain_password=connection_string,
            ssl_context=ssl_context,
            client_id='python-producer',
        )
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def send_json(self, topic: str, payload: dict[str, Any]) -> None:
        if not self._producer:
            raise RuntimeError('Producer not started')
        await self._producer.send_and_wait(topic, json.dumps(payload).encode('utf-8'))
