from clickhouse_app.client import get_clickhouse_client
from config import CLICKHOUSE_TABLE_USERS


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
