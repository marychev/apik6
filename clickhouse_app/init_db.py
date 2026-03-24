from clickhouse_app.client import get_clickhouse_client


def init_tables():
    client = get_clickhouse_client()
    client.command("""
        CREATE TABLE IF NOT EXISTS users (
            id String,
            name String,
            email String,
            created_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY created_at
    """)
