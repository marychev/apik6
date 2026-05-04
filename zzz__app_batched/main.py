"""
Прототип FastAPI + aiokafka + cross-request coalescing через asyncio.Queue.

Поток данных:
  Handler: await queue.put(user)        # backpressure если очередь полна
  Batcher: drain(queue) до BATCH_MAX    # асинхронный фоновый task из lifespan
           await asyncio.gather(send x N)  # параллельная отправка

Отличия от baseline (app/):
- Handler НЕ зовёт producer.send() — только кладёт в Queue и возвращает 200.
- Все Kafka-send'ы идут из ОДНОГО фонового task'а, batch'ами до 100 штук.
- Ошибки aiokafka ловятся в gather-awaitе и логируются — не теряются силентно как в F&F через create_task.

Trade-off: в случае краша воркера в Queue могут зависнуть ≤ QUEUE_MAX_SIZE сообщений.
"""
import asyncio
import os
import uuid
from contextlib import asynccontextmanager

import orjson
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI
from pydantic import BaseModel

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "users"
QUEUE_MAX_SIZE = 10_000
BATCH_MAX_SIZE = 100


class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str


def prepare_user(user: UserCreate) -> UserResponse:
    return UserResponse(id=str(uuid.uuid4()), name=user.name, email=user.email)


producer: AIOKafkaProducer | None = None
queue: asyncio.Queue | None = None
batcher_task: asyncio.Task | None = None


async def _batcher() -> None:
    """Дрейнит очередь, отправляет пачку через asyncio.gather."""
    while True:
        try:
            first = await queue.get()
        except asyncio.CancelledError:
            return
        batch = [first]
        while len(batch) < BATCH_MAX_SIZE:
            try:
                batch.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        try:
            results = await asyncio.gather(
                *[
                    producer.send(KAFKA_TOPIC, key=u.id, value=u.model_dump())
                    for u in batch
                ],
                return_exceptions=True,
            )
            failed = [r for r in results if isinstance(r, Exception)]
            if failed:
                print(
                    f"[batcher] {len(failed)}/{len(batch)} sends failed: "
                    f"{type(failed[0]).__name__}: {failed[0]}",
                    flush=True,
                )
        except Exception as e:
            print(f"[batcher] batch error: {type(e).__name__}: {e}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer, queue, batcher_task
    queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
    producer = AIOKafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_serializer=orjson.dumps,
        key_serializer=lambda k: k.encode("utf-8"),
        linger_ms=20,
        max_batch_size=65536,
        compression_type="lz4",
        acks=1,
    )
    await producer.start()
    batcher_task = asyncio.create_task(_batcher())
    yield
    if batcher_task:
        batcher_task.cancel()
    if producer:
        await producer.flush()
        await producer.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/users/batch/{n}")
async def batch(n: int = 1) -> dict:
    for i in range(1, n + 1):
        user = prepare_user(
            UserCreate(name=f"user_{i}", email=f"user_{i}@example.com")
        )
        await queue.put(user)
    return {"sent": n}
