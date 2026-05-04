"""
Прототип FastAPI + confluent-kafka-python (librdkafka через Python C-extension).

Отличия от baseline (app/):
- Producer: confluent_kafka.Producer (sync API, C background thread) вместо aiokafka.
- produce() не блокирует event loop — librdkafka батчит и шлёт в отдельном C-потоке, GIL отпускается.
- Периодический poll(0) в фоне разгребает internal delivery queue.

FastAPI/pydantic/orjson/workers — идентично baseline, чтобы изолировать только Kafka-слой.
"""
import asyncio
import os
import uuid
from contextlib import asynccontextmanager

import orjson
from confluent_kafka import Producer
from fastapi import FastAPI
from pydantic import BaseModel

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "users"

PRODUCER_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "linger.ms": 20,
    "batch.size": 65536,
    "compression.type": "lz4",
    "acks": "1",
}


class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str


def prepare_user(user: UserCreate) -> UserResponse:
    return UserResponse(id=str(uuid.uuid4()), name=user.name, email=user.email)


producer: Producer | None = None
_poll_task: asyncio.Task | None = None


async def _poll_loop(p: Producer) -> None:
    try:
        while True:
            p.poll(0)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, _poll_task
    producer = Producer(PRODUCER_CONFIG)
    _poll_task = asyncio.create_task(_poll_loop(producer))
    yield
    if _poll_task:
        _poll_task.cancel()
    if producer:
        producer.flush(10)


app = FastAPI(lifespan=lifespan)


@app.post("/users/batch/{n}")
async def batch(n: int = 1) -> dict:
    for i in range(1, n + 1):
        user = prepare_user(
            UserCreate(name=f"user_{i}", email=f"user_{i}@example.com")
        )
        producer.produce(
            KAFKA_TOPIC,
            key=user.id,
            value=orjson.dumps(user.model_dump()),
        )
    return {"sent": n}
