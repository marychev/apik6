import json

from kafka import KafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS

_producer: KafkaProducer | None = None


def get_producer() -> KafkaProducer:
    """
    Продюсер создаётся один раз и переиспользуется (ленивая инициализация) 
    Без этого каждый вызов создавал бы новое TCP-соединение к Kafka — это дорого. 
    """
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
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
