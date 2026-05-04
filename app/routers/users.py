import uuid
from fastapi import APIRouter, Request

from clickhouse_app.client import get_clickhouse_client
from config import CLICKHOUSE_TABLE_USERS, KAFKA_TOPIC_USERS
# from kafka_app.user_producer import send_users_batch
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/count")
def count() -> dict:
    client = get_clickhouse_client()
    result = client.query(f"SELECT count() FROM {CLICKHOUSE_TABLE_USERS}")
    return {"count": result.first_row[0]}


@router.post("/batch/{n}")
async def batch(request: Request, n: int = 1) -> dict:
    if n > 1:
        raise ValueError("Only batch of 1 user is supported in this example")

    pk = str(uuid.uuid4())
    user = UserResponse(id=pk, name=f"user_{pk}", email=f"user_{pk}@example.com")

    producer = request.app.state.kafka_producer

    await producer.send(
        KAFKA_TOPIC_USERS, key=user.id, value=user.model_dump()
    )

    return {"sent": 1}
