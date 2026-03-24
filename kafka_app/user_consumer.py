import logging

from kafka_app.consumer import get_consumer

logger = logging.getLogger(__name__)

TOPIC = "users"
GROUP_ID = "user-service"


def consume_users() -> None:
    consumer = get_consumer(TOPIC, GROUP_ID)
    logger.info("Listening to Kafka topic '%s'...", TOPIC)
    print(f"[consumer] Listening to topic '{TOPIC}'...")

    for message in consumer:
        user_data = message.value
        print(f"[consumer] Received user: {user_data['id']} - {user_data['name']} (offset={message.offset})")
