import logging

from kafka_app.consumer import get_consumer
from clickhouse_app.client import get_clickhouse_client

logger = logging.getLogger(__name__)

TOPIC = "users"
GROUP_ID = "user-clickhouse"

_consumer = None


def _get_consumer():
    global _consumer
    if _consumer is None:
        _consumer = get_consumer(TOPIC, GROUP_ID)
    return _consumer


def consume_users_to_clickhouse(expected: int, timeout_ms: int = 10000) -> int:
    client = get_clickhouse_client()
    consumer = _get_consumer()

    rows = []
    while len(rows) < expected:
        batch = consumer.poll(timeout_ms=timeout_ms)
        if not batch:
            break
        for messages in batch.values():
            for message in messages:
                user_data = message.value
                rows.append([user_data["id"], user_data["name"], user_data["email"]])

    if rows:
        client.insert("users", rows, column_names=["id", "name", "email"])

    logger.info("Consumed %d users from Kafka → ClickHouse", len(rows))
    return len(rows)
