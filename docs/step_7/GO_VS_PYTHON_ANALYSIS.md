# Анализ: Go vs Python — ключевая разница для 5k RPS

## Сравнение конфигураций

### Go (franz-go) vs Python (aiokafka)

| Параметр | Go | Python | Примечание |
|----------|-----|--------|-----------|
| **Broker library** | franz-go (native Go) | aiokafka (Python async) | Franz скомпилирована в машинный код, aiokafka интерпретируется |
| **linger_ms** | 20ms | 20ms | Одинаково |
| **batch_size** | 64KB | 64KB | Одинаково (но можно 128KB) |
| **compression** | LZ4 | LZ4 | Одинаково |
| **acks** | LeaderAck (=1) | acks=1 | Одинаково |
| **Idempotent writes** | ❌ ОТКЛЮЧЕНО (`DisableIdempotentWrite()`) | ⚠️ **ВКЛЮЧЕНО** (default) | 🔑 **ВОЗМОЖНОЕ УЗКОЕ МЕСТО** |
| **Thread model** | goroutines + channels | async/await | Go горутины легче питоновых async |
| **HTTP server** | net/http (встроен) | FastAPI + uvicorn | Питон добавляет overhead |

## Что такое idempotent writes?

### Если ВКЛЮЧЕНЫ (Python default)
- Каждый message получает уникальный **PID (Producer ID)** + **sequence number**
- Broker проверяет дубликаты перед записью
- **Больше логики на producer-е и broker-е** → медленнее
- Гарантирует ровно-одну доставку (exactly-once semantics)

### Если ОТКЛЮЧЕНЫ (Go)
- Никаких PID/sequence — просто пишется сообщение
- Меньше overhead на отправку
- **Быстрее!**
- Гарантирует at-least-once (возможны редкие дубли)

**Это может объяснить разницу 3-4x между Go и Python!**

---

## План оптимизации: 4 шага к 5k RPS

### Шаг 1: Отключить idempotent writes в Python

```python
# kafka_app/producer.py
async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_serializer=lambda v: orjson.dumps(v),
        key_serializer=lambda k: k.encode("utf-8"),
        linger_ms=100,          # 20 → 100 (больше время для батчинга)
        max_batch_size=131072,  # 64KB → 128KB
        compression_type="lz4",
        acks=1,
        idempotent=False,       # 🔑 **ОТКЛЮЧАЕМ** — ключевая оптимизация
    )
    await producer.start()
    return producer
```

### Шаг 2: Увеличить параллелизм Kafka

```python
# config.py
KAFKA_ENGINE_NUM_CONSUMERS = 8  # 4 → 8
```

```yaml
# docker-compose.yml
environment:
  KAFKA_NUM_PARTITIONS: ${KAFKA_NUM_PARTITIONS:-8}  # 4 → 8
  KAFKA_ENGINE_NUM_CONSUMERS: 8
  UVICORN_WORKERS: 4  # 5 → 4 (ровно логические потоки)
```

### Шаг 3: Обновить ClickHouse settings

```python
# config.py
KAFKA_ENGINE_NUM_CONSUMERS = 8
KAFKA_ENGINE_POLL_TIMEOUT_MS = 1000
KAFKA_ENGINE_POLL_MAX_BATCH_SIZE = 200000
KAFKA_ENGINE_FLUSH_INTERVAL_MS = 10000
```

### Шаг 4: Пересоздать инфраструктуру

```bash
# Полная очистка
make full-clean && make up

# Увеличить партиции (важно!)
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --alter --topic users --partitions 8
```

---

## Прогноз результатов

| Параметр | Текущее | После оптимизации |
|----------|---------|------------------|
| **idempotent** | True | **False** |    
| **linger_ms** | 20ms | **100ms** |    
| **batch_size** | 64KB | **128KB** |   
| **partitions** | 4 | **8** |
| **consumers** | 4 | **8** |
| **workers** | 5 | **4** |              
| **Прогноз RPS** | ~3k | **~4.5-5.5k ✅** |
| **Прогноз p95** | ~1.5s | **~1.0-1.2s ✅** |

## Почему это должно работать

1. ✅ **idempotent=False** удаляет основной overhead Kafka Producer (как в Go)
2. ✅ **Больше партиций (4→8)** = распределение нагрузки
3. ✅ **Больше linger** = лучше батчинг, меньше flush'ей
4. ✅ **Больше потребителей** = ClickHouse читает быстрее
5. ✅ **Оптимальное число воркеров** = меньше контекст-switching

## Риски и оговорки

⚠️ **idempotent=False** → возможны дубликаты (at-least-once вместо exactly-once)
   - Для тестовых данных пользователей = приемлемо
   - Для production нужна application-level deduplication

🚩 **Если работает** → мы нашли корень проблемы (Kafka overhead в Python)
🚩 **Если не работает** → bottleneck глубже (ClickHouse, CPU, memory)

---

## Тестирование

```bash
# Запуск нагрузки
k6 run --vus 2500 --duration 1m k6/rps.js

# Проверка данных
docker compose exec clickhouse clickhouse-client --query="SELECT count() FROM users"

# Сравнение медиан
# ДО:  RPS ~3k, p95 ~1.5s
# ПОСЛЕ: RPS ~5k?, p95 ~1.2s?
```

## Следующие шаги

Если 5k не получится:
1. Проверить CPU usage (top, docker stats)
2. Проверить Kafka broker metrics (lags, ISR)
3. Проверить ClickHouse insert rates (system.parts)
4. Рассмотреть асинхронные операции в ClickHouse consumer
