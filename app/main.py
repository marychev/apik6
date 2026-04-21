from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.users import router as users_router
from clickhouse_app.init_db import init_tables
from kafka_app.producer import create_producer, close_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tables()
    app.state.kafka_producer = await create_producer()
    yield
    await close_producer(app.state.kafka_producer)


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
