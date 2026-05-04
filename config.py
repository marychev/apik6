import os

# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_USERS = "users"

# aiokafka producer tuning
_acks_raw = os.getenv("KAFKA_PRODUCER_ACKS", "1")
KAFKA_PRODUCER_LINGER_MS = int(os.getenv("KAFKA_PRODUCER_LINGER_MS", "20"))
KAFKA_PRODUCER_BATCH_SIZE = int(os.getenv("KAFKA_PRODUCER_BATCH_SIZE", "65536"))
KAFKA_PRODUCER_COMPRESSION = os.getenv("KAFKA_PRODUCER_COMPRESSION", "lz4")
KAFKA_PRODUCER_ACKS = _acks_raw if _acks_raw == "all" else int(_acks_raw)
KAFKA_PRODUCER_IDEMPOTENT = os.getenv("KAFKA_PRODUCER_IDEMPOTENT", "true").lower() == "true"

# ClickHouse Kafka engine tuning
# kafka_num_consumers не должен превышать число партиций в топике.
KAFKA_ENGINE_NUM_CONSUMERS = int(os.getenv("KAFKA_ENGINE_NUM_CONSUMERS", "4"))
KAFKA_ENGINE_POLL_TIMEOUT_MS = int(os.getenv("KAFKA_ENGINE_POLL_TIMEOUT_MS", "1000"))
KAFKA_ENGINE_POLL_MAX_BATCH_SIZE = int(os.getenv("KAFKA_ENGINE_POLL_MAX_BATCH_SIZE", "200000"))
KAFKA_ENGINE_FLUSH_INTERVAL_MS = int(os.getenv("KAFKA_ENGINE_FLUSH_INTERVAL_MS", "10000"))

# ClickHouse
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_TABLE_USERS = "users"
