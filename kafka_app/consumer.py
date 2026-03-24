import json

from kafka import KafkaConsumer

from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_AUTO_OFFSET_RESET


def get_consumer(topic: str, group_id: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        group_id=group_id,
        auto_offset_reset=KAFKA_AUTO_OFFSET_RESET,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
