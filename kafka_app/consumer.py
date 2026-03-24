import json

from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = "kafka:9092"


def get_consumer(topic: str, group_id: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=[BOOTSTRAP_SERVERS],
        group_id=group_id,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
