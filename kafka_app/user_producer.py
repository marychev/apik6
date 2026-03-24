import logging

from kafka_app.producer import get_producer
from config import KAFKA_TOPIC_USERS

logger = logging.getLogger(__name__)


def send_users_batch(users) -> int:
    
    # 2. Отправка пачкой
    producer = get_producer()
    for user in users:
        producer.send(KAFKA_TOPIC_USERS, key=user.id, value=user.model_dump())
    producer.flush()
    n = len(users)
    
    logger.info("Sent batch of %d users to Kafka topic '%s'", n, KAFKA_TOPIC_USERS)
    return n
