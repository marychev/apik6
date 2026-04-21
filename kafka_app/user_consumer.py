# ============================================================================
# ОТКЛЮЧЕНО в step_4: заменено на ClickHouse Kafka Engine + MaterializedView.
# Схема теперь создаётся в clickhouse_app/init_db.py (users_kafka + users_mv).
# Оставлено как reference / для отката к Python-consumer'у при необходимости.
# ============================================================================

# import logging
#
# from kafka_app.consumer import get_consumer
# from clickhouse_app.client import get_clickhouse_client
# from clickhouse_app.init_db import init_tables
# from config import KAFKA_TOPIC_USERS, KAFKA_CONSUMER_GROUP_USERS, KAFKA_CONSUMER_TIMEOUT_MS, CLICKHOUSE_TABLE_USERS
#
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# BATCH_SIZE = 1000
#
#
# def run_consumer() -> None:
#     init_tables()
#     client = get_clickhouse_client()
#     consumer = get_consumer(KAFKA_TOPIC_USERS, KAFKA_CONSUMER_GROUP_USERS)
#
#     logger.info("Consumer started. Listening to topic '%s'...", KAFKA_TOPIC_USERS)
#
#     buffer = []
#
#     while True:
#         batch = consumer.poll(timeout_ms=KAFKA_CONSUMER_TIMEOUT_MS)
#
#         for messages in batch.values():
#             for message in messages:
#                 user_data = message.value
#                 buffer.append([user_data["id"], user_data["name"], user_data["email"]])
#
#         # Flush buffer when full or when we got data and no more is coming
#         if len(buffer) >= BATCH_SIZE or (buffer and not batch):
#             client.insert(CLICKHOUSE_TABLE_USERS, buffer, column_names=["id", "name", "email"])
#             logger.info("Inserted %d users into ClickHouse", len(buffer))
#             buffer.clear()
#
#
# if __name__ == "__main__":
#     run_consumer()
