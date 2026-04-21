from aiokafka import AIOKafkaProducer

from app.schemas import UserResponse
from config import KAFKA_TOPIC_USERS


async def send_users_batch(
    producer: AIOKafkaProducer, users: list[UserResponse]
) -> int:
    for user in users:
        await producer.send(
            KAFKA_TOPIC_USERS, key=user.id, value=user.model_dump()
        )
    return len(users)
