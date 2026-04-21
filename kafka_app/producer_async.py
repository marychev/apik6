"""
Async-версия продюсера на aiokafka.

Отличия от sync producer.py:
1. AIOKafkaProducer вместо KafkaProducer
2. await producer.start() нужен для инициализации (внутри — создание event loop задач)
3. await producer.stop() при завершении — корректно сбрасывает буфер
4. Singleton не через глобальную переменную — aiokafka привязан к event loop,
   поэтому продюсер создаётся через FastAPI lifespan и хранится в app.state

Почему sync singleton здесь не работает:
- aiokafka использует asyncio под капотом
- При первом вызове в каждом воркере нужен running event loop
- FastAPI lifespan — стандартный способ управления async-ресурсами
"""
import json

from aiokafka import AIOKafkaProducer

from config import KAFKA_BOOTSTRAP_SERVERS


async def create_producer() -> AIOKafkaProducer:
    """
    Создаёт и стартует async-продюсер.
    Вызывается один раз при старте FastAPI (через lifespan).
    """
    producer = AIOKafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
    )
    await producer.start()
    return producer


async def close_producer(producer: AIOKafkaProducer) -> None:
    """
    Корректно останавливает продюсер:
    - сбрасывает оставшиеся в буфере сообщения
    - закрывает TCP-соединения
    Вызывается один раз при остановке FastAPI (через lifespan).
    """
    await producer.stop()
