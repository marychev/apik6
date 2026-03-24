from fastapi import APIRouter

from app.schemas import UserCreate, UserResponse
from app.services import prepare_user, get_users_count, reset_users
from kafka_app.user_producer import send_user_created, send_users_batch
from kafka_app.user_consumer import consume_users_to_clickhouse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
def create(user: UserCreate):
    user_data = prepare_user(user.name, user.email)
    send_user_created(user_data)
    return user_data


@router.get("/count")
def count():
    return {"count": get_users_count()}


@router.post("/batch/{n}")
def batch(n: int = 1000):
    # 1. Подготовка + отправка в Kafka
    sent = send_users_batch(n)
    # 2. Чтение из Kafka → запись в ClickHouse
    saved = consume_users_to_clickhouse(expected=sent)
    return {"sent": sent, "saved_to_clickhouse": saved}


@router.post("/reset", status_code=204)
def reset():
    reset_users()
