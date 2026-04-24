import os
import uuid
from contextlib import asynccontextmanager

import orjson
from aiokafka import AIOKafkaProducer
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "users"

producer: AIOKafkaProducer | None = None


@asynccontextmanager
async def lifespan(app):
    global producer
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
    yield
    await producer.stop()


async def batch(request):
    n = request.path_params["n"]
    for i in range(1, n + 1):
        uid = str(uuid.uuid4())
        value = {"id": uid, "name": f"user_{i}", "email": f"user_{i}@example.com"}
        await producer.send(KAFKA_TOPIC, key=uid, value=value)
    return Response(orjson.dumps({"sent": n}), media_type="application/json")


app = Starlette(
    lifespan=lifespan,
    routes=[Route("/users/batch/{n:int}", batch, methods=["POST"])],
)
