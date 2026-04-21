"""
Async-версия точки входа FastAPI.

Ключевая часть — lifespan:
- при старте приложения создаётся AIOKafkaProducer и сохраняется в app.state
- при остановке — корректно закрывается (сбрасывает буфер, закрывает TCP)

Каждый воркер uvicorn запустит этот lifespan отдельно — у каждого свой
продюсер, привязанный к своему event loop'у.

Запуск для теста:
  uvicorn app.main_async:app --workers 4 --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.users_async import router as users_router
from kafka_app.producer_async import create_producer, close_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.kafka_producer = await create_producer()
    yield
    # shutdown
    await close_producer(app.state.kafka_producer)


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
