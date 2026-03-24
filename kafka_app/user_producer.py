import logging

from kafka_app.producer import get_producer
from app.services import prepare_user

logger = logging.getLogger(__name__)

TOPIC = "users"


def send_user_created(user_data: dict) -> None:
    producer = get_producer()
    producer.send(TOPIC, key=str(user_data["id"]), value=user_data)
    logger.info("Sent user %s to Kafka topic '%s'", user_data["id"], TOPIC)


def send_users_batch(n: int = 1000) -> int:
    # 1. Подготовка данных
    users = [
        prepare_user(f"user_{i}", f"user_{i}@example.com")
        for i in range(1, n + 1)
    ]

    # 2. Отправка пачкой
    producer = get_producer()
    for user_data in users:
        producer.send(TOPIC, key=user_data["id"], value=user_data)
    producer.flush()

    logger.info("Sent batch of %d users to Kafka topic '%s'", n, TOPIC)
    return n
