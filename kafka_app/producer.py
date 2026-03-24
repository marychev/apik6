import json

from kafka import KafkaProducer

BOOTSTRAP_SERVERS = "kafka:9092"

_producer: KafkaProducer | None = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=[BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8"),
        )
    return _producer


def close_producer() -> None:
    global _producer
    if _producer:
        _producer.flush()
        _producer.close()
        _producer = None
