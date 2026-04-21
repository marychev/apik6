from clickhouse_app.client import get_clickhouse_client
from config import (
    CLICKHOUSE_TABLE_USERS,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_USERS,
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
            kafka_num_consumers = 1,
            kafka_poll_timeout_ms = 5000,
            kafka_poll_max_batch_size = 500000,
            kafka_flush_interval_ms = 15000
    """)

    client.command(f"""
        CREATE MATERIALIZED VIEW IF NOT EXISTS {CLICKHOUSE_TABLE_USERS}_mv
        TO {CLICKHOUSE_TABLE_USERS}
        AS SELECT id, name, email FROM {CLICKHOUSE_TABLE_USERS}_kafka
    """)
