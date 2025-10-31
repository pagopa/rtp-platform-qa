"""Compatibility shim for legacy imports of setup_producer().

Prefer using services.producer.ProducerService in new code.
"""
from services.producer import ProducerService


async def setup_producer():
    """Start a ProducerService and return the underlying AIOKafkaProducer.

    This preserves the old behavior where callers expected an AIOKafkaProducer
    instance with .send_and_wait() and .stop().
    """
    svc = ProducerService()
    await svc.start()
    # Fail fast if initialization didn't create the underlying producer
    if svc._producer is None:
        raise RuntimeError(
            "ProducerService failed to initialize the producer. _producer is None after start()."
        )

    return svc._producer
