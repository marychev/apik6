import logging

from aiokafka import AIOKafkaProducer

from app.schemas import UserResponse
from config import KAFKA_TOPIC_USERS

logger = logging.getLogger(__name__)


async def send_users_batch(
    producer: AIOKafkaProducer, users: list[UserResponse]
) -> int:
    for user in users:
        await producer.send(
            KAFKA_TOPIC_USERS, key=user.id, value=user.model_dump()
        )
    await producer.flush()
    n = len(users)
    logger.info(
        "Sent batch of %d users to Kafka topic '%s'", n, KAFKA_TOPIC_USERS
    )
    return n
