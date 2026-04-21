"""
Async-продюсер на aiokafka.

Singleton создаётся через FastAPI lifespan и хранится в app.state —
привязка к event loop требует инициализации в async контексте.
"""
import json

from aiokafka import AIOKafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        linger_ms=20,
        max_batch_size=65536,
        compression_type="lz4",
        acks=1,
    )
    await producer.start()
    return producer


async def close_producer(producer: AIOKafkaProducer) -> None:
    await producer.stop()
