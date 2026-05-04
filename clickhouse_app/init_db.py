from clickhouse_app.client import get_clickhouse_client
from config import (
    CLICKHOUSE_TABLE_USERS,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_USERS,
    KAFKA_ENGINE_NUM_CONSUMERS,
    KAFKA_ENGINE_POLL_TIMEOUT_MS,
    KAFKA_ENGINE_POLL_MAX_BATCH_SIZE,
    KAFKA_ENGINE_FLUSH_INTERVAL_MS,
)


def init_tables():
    client = get_clickhouse_client()

    client.command(f"""
        CREATE TABLE IF NOT EXISTS {CLICKHOUSE_TABLE_USERS} (
            id String,
            name String,
            email String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY created_at
    """)

    client.command(f"""
        CREATE TABLE IF NOT EXISTS {CLICKHOUSE_TABLE_USERS}_kafka (
            id String,
            name String,
            email String
        ) ENGINE = Kafka
        SETTINGS
            kafka_broker_list = '{KAFKA_BOOTSTRAP_SERVERS}',
            kafka_topic_list = '{KAFKA_TOPIC_USERS}',
            kafka_group_name = 'clickhouse_users',
            kafka_format = 'JSONEachRow',
            kafka_num_consumers = {KAFKA_ENGINE_NUM_CONSUMERS},
            kafka_poll_timeout_ms = {KAFKA_ENGINE_POLL_TIMEOUT_MS},
            kafka_poll_max_batch_size = {KAFKA_ENGINE_POLL_MAX_BATCH_SIZE},
            kafka_flush_interval_ms = {KAFKA_ENGINE_FLUSH_INTERVAL_MS}
    """)

    client.command(f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS {CLICKHOUSE_TABLE_USERS}_mv
        TO {CLICKHOUSE_TABLE_USERS}
        AS SELECT id, name, email FROM {CLICKHOUSE_TABLE_USERS}_kafka
    """)
