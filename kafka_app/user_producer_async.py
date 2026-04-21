"""
Async-версия отправки пользователей в Kafka.

Ключевое отличие от sync версии:
- producer.send() возвращает Future, а не отправляет сразу
- await producer.flush() отдаёт управление event loop'у на время ожидания ACK
- пока этот запрос ждёт Kafka, воркер обрабатывает другие запросы

В sync-версии воркер полностью заблокирован на flush() — обрабатывает 1 запрос.
В async-версии один воркер может одновременно обрабатывать сотни запросов,
пока они ждут Kafka.
"""
import logging

from aiokafka import AIOKafkaProducer

from app.schemas import UserResponse
from config import KAFKA_TOPIC_USERS

logger = logging.getLogger(__name__)


async def send_users_batch(
    producer: AIOKafkaProducer, users: list[UserResponse]
) -> int:
    """
    Отправляет батч пользователей в Kafka асинхронно.

    Продюсер передаётся явно (через DI), а не берётся из глобальной переменной,
    потому что aiokafka привязан к конкретному event loop'у FastAPI.
    """
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
