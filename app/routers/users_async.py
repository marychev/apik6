"""
Async-версия роутера.

Отличия от sync users.py:
1. async def batch() — эндпоинт корутина
2. await send_users_batch(...) — не блокирует воркер на flush()
3. Продюсер берётся из request.app.state (инициализирован в lifespan)

Пока этот запрос ждёт Kafka ACK, тот же воркер обрабатывает другие запросы.
Это превращает concurrency с "4 параллельных запроса" (4 воркера) в "сотни".
"""
from fastapi import APIRouter, Request

from app.schemas import UserCreate
from app.services import prepare_user
from clickhouse_app.client import get_clickhouse_client
from config import CLICKHOUSE_TABLE_USERS
from kafka_app.user_producer_async import send_users_batch

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/count")
def count() -> dict:
    client = get_clickhouse_client()
    result = client.query(f"SELECT count() FROM {CLICKHOUSE_TABLE_USERS}")
    return {"count": result.first_row[0]}


@router.post("/batch/{n}")
async def batch(request: Request, n: int = 1) -> dict:
    users = [
        prepare_user(UserCreate(name=f"user_{i}", email=f"user_{i}@example.com"))
        for i in range(1, n + 1)
    ]

    producer = request.app.state.kafka_producer
    sent = await send_users_batch(producer, users)

    return {"sent": sent}
