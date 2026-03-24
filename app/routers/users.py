from fastapi import APIRouter

from app.schemas import UserCreate
from app.services import prepare_user
from kafka_app.user_producer import send_users_batch

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/batch/{n}")
def batch(n: int = 1) -> dict:
    # 1. Подготовка данных
    users = [
        prepare_user(UserCreate(name=f"user_{i}", email=f"user_{i}@example.com"))
        for i in range(1, n + 1)
    ]

    # 2. Отправка в Kafka
    sent = send_users_batch(users)

    # 3. Запись в ClickHouse происходит в другом процессе (докер-контейнер).
    #  Запускается consumer_users_batch_to_clickhouse() как как бесконечный цикл 
    # — он постоянно слушает Kafka и пишет в ClickHouse по мере поступления данных.
    
    return {"sent": sent}
