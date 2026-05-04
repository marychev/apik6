"""
Async-продюсер на aiokafka.

Singleton создаётся через FastAPI lifespan и хранится в app.state —
привязка к event loop требует инициализации в async контексте.
"""
import orjson

from aiokafka import AIOKafkaProducer

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_PRODUCER_LINGER_MS,
    KAFKA_PRODUCER_BATCH_SIZE,
    KAFKA_PRODUCER_COMPRESSION,
    KAFKA_PRODUCER_ACKS,
    KAFKA_PRODUCER_IDEMPOTENT,
)


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_serializer=lambda v: orjson.dumps(v),
        key_serializer=lambda k: k.encode("utf-8"),
        linger_ms=KAFKA_PRODUCER_LINGER_MS,
        max_batch_size=KAFKA_PRODUCER_BATCH_SIZE,
        compression_type=KAFKA_PRODUCER_COMPRESSION,
        acks=KAFKA_PRODUCER_ACKS,
        enable_idempotence=KAFKA_PRODUCER_IDEMPOTENT,
    )
    await producer.start()
    return producer


async def close_producer(producer: AIOKafkaProducer) -> None:
    await producer.stop()
