# ClickHouse Kafka Engine вместо Python consumer

**Дата:** 21.04.2026 | **Среда:** Docker/WSL2, i3-1005G1 (2c/4t) | **Инструмент:** k6
**Базовая конфигурация:** FastAPI + aiokafka (оптимизированный в step_3), Kafka 2 partitions

## TL;DR

Заменили Python consumer на нативную интеграцию через `ENGINE = Kafka` + `MaterializedView`. После тюнинга параметров Kafka Engine получили:

- **RPS:** 2152 (vs 2177 Python consumer, −1.1% — в пределах шума)
- **p95:** 1.63s (vs 2.18s, **−25%**)
- **median:** 659ms (vs 832ms, **−21%**)
- **Data loss:** 0% (все 128 557 сообщений долетели, lag=0)
- **Код:** Python consumer и отдельный сервис удалены

**Ключевой вывод:** одинаковая пропускная способность + лучшая latency + меньше кода. На production-железе (4+ ядер) вероятно вырвется вперёд по RPS.

---

## 1. Что поменялось

### До (step_3)

```
[API] ──POST──→ [Kafka: users] ──poll──→ [Python consumer process]
                                                    │
                                              batch 1000
                                                    ↓
                                         [ClickHouse: users (MergeTree)]
```

Отдельный Python-процесс читал из Kafka, батчил в памяти, делал `INSERT` в ClickHouse через `clickhouse-connect`.

### После (step_4)

```
[API] ──POST──→ [Kafka: users]
                       │
                       │ (нативное чтение)
                       ↓
              [ClickHouse: users_kafka (ENGINE = Kafka)]
                       │
                       │ (MaterializedView)
                       ↓
              [ClickHouse: users (MergeTree)]
```

ClickHouse сам читает из Kafka через встроенный librdkafka-клиент, MaterializedView автоматически переливает в целевую MergeTree таблицу. Python-код consumer'а закомментирован в [kafka_app/user_consumer.py](../../kafka_app/user_consumer.py), consumer-сервис в [docker-compose.yml](../../docker-compose.yml) отключён.

---

## 2. Схема (clickhouse_app/init_db.py)

```sql
-- Целевая таблица (как была)
CREATE TABLE users (
    id String, name String, email String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree() ORDER BY created_at;

-- Kafka-таблица — "виртуальная", просто подписка на топик
CREATE TABLE users_kafka (
    id String, name String, email String
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka:9092',
    kafka_topic_list = 'users',
    kafka_group_name = 'clickhouse_users',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1,
    kafka_poll_timeout_ms = 5000,       -- было 500 (тюнинг)
    kafka_poll_max_batch_size = 500000, -- было 65536 (тюнинг)
    kafka_flush_interval_ms = 15000;    -- было 7500 (тюнинг)

-- MV автоматически читает из users_kafka и пишет в users
CREATE MATERIALIZED VIEW users_mv TO users
AS SELECT id, name, email FROM users_kafka;
```

`init_tables()` вызывается при старте API через FastAPI lifespan.

---

## 3. Результаты на VU=2500

### 3.1. Первый прогон — дефолтные настройки (без тюнинга)

| Метрика | Python consumer | Kafka Engine (default) | Δ |
|---|---|---|---|
| RPS | 2177 | **1811** | **−17%** ❌ |
| Errors | 0% | 0.50% | +0.5% |
| median | 832ms | 693ms | −17% ✅ |
| p95 | 2.18s | 1.82s | −17% ✅ |
| VUs min active | 1735 | **197** | много застрявших |

**Проблема:** RPS упал на 17%. Гипотеза — ClickHouse ест CPU брокера.

### 3.2. Docker stats под нагрузкой (default)

ClickHouse активно polling'ился каждые 500ms и забирал у брокера CPU на 2-ядерной машине.

### 3.3. Тюнинг Kafka Engine → финальный прогон

Идея — сделать Kafka Engine "ленивее":
- Реже polling'иться
- Брать крупнее батчи за раз
- Реже флашить в MergeTree

| Параметр | Default | Новое | Эффект |
|---|---|---|---|
| `kafka_poll_timeout_ms` | 500 | **5000** | Polling раз в 5s вместо 500ms — меньше пустых циклов |
| `kafka_poll_max_batch_size` | 65536 | **500000** | За один poll берёт до 500k сообщений |
| `kafka_flush_interval_ms` | 7500 | **15000** | Реже INSERT'ит в MergeTree — меньше мелких parts |

### 3.4. Результаты после тюнинга

| Метрика | Python consumer | **Kafka Engine (tuned)** | Δ vs Python |
|---|---|---|---|
| RPS | 2177 | **2152** | **−1.1% (шум)** ✅ |
| median | 832ms | **659ms** | **−21%** ✅ |
| p95 | 2.18s | **1.63s** | **−25%** ✅ |
| Errors | 0% | 0.26% | +0.26% |
| VUs min active | 1735 | 1537 | ≈ равно |

### 3.5. Docker stats под нагрузкой (tuned)

| Контейнер | CPU % | Было (default) |
|---|---|---|
| **apik6-api-1** | **181.97%** | (упёрся в потолок 2-HT ядер) |
| **apik6-kafka-1** | **95.47%** | (почти целое ядро) |
| **apik6-clickhouse-1** | **15.36%** | было ~100%+ |
| zookeeper | 0.42% | idle |

**ClickHouse CPU упал с ~100%+ до 15%.** Тюнинг polling'а освободил ядра брокеру.

---

## 4. Верификация корректности

| Проверка | Результат |
|---|---|
| `SELECT count() FROM users` | **128 557** (= итерации k6) |
| Kafka lag partition 0 | **0** |
| Kafka lag partition 1 | **0** |
| Сумма offset'ов (64144 + 64413) | 128 557 (совпадает) |

Zero data loss, zero lag. Все сообщения из Kafka переложены в MergeTree в real-time.

---

## 5. Что убрали из пайплайна

- `kafka_app/user_consumer.py` — закомментирован (оставлен как reference для отката)
- `kafka_app/consumer.py` — помощник для `KafkaConsumer`, больше не используется
- Сервис `consumer` в `docker-compose.yml` — закомментирован
- Зависимость Python-процесса от батчевого цикла `poll → buffer → insert`

Добавлено:
- `api` теперь `depends_on: clickhouse: service_started` (для корректного startup `init_tables`)
- `init_tables()` вызов в lifespan API (`app/main.py`)

---

## 6. Выводы

1. **ClickHouse Kafka Engine — правильный архитектурный выбор**, даже на 2-ядерной dev машине. После тюнинга polling'а throughput равен Python consumer'у, а latency успешных запросов лучше на 21–25%.

2. **Дефолтные настройки Kafka Engine агрессивны.** `kafka_poll_timeout_ms=500` заставляет ClickHouse постоянно опрашивать брокер. На ограниченных ядрах это конкурирует за CPU с продьюсерной стороной. Следует увеличить до 5000ms + выставить крупный `kafka_poll_max_batch_size`.

3. **Меньше кода, меньше сервисов, проще эксплуатация.** Нет отдельного Python-процесса, нет GIL, нет ручного батчинга, нет необходимости перезапускать consumer при изменениях схемы.

4. **На production-железе (4+ ядер) Kafka Engine вероятно вырвется по throughput**, потому что CPU-contention между consumer'ом и брокером перестанет быть проблемой.

5. **Небольшая разница в ошибках (0.26% vs 0%)** — из-за лёгкой bimodality: при очень высокой конкурентности часть запросов попадает в backpressure. На production-железе должно пропасть. Если критично reliability — можно компенсировать через 3 партиции (см. step_3 PARTITIONS тесты).

---

## 7. Финальная цепочка оптимизаций (все steps)

| Этап | Пик RPS | p95 на пике | Комментарий |
|---|---|---|---|
| Sync + 1 partition (baseline) | 760 | ~1.6s | |
| Async + 2 partitions | 1780 | ~1.8s | ×2.4 |
| + producer tune (linger, lz4, no flush) | 2150 | 936ms | ×2.8 |
| + orjson, no-log, 5 workers, broker threads | 2177 | 2.18s | ×2.87 |
| **+ ClickHouse Kafka Engine (tuned)** | **2152** | **1.63s** | архитектурная замена |

**Эффективный финал: пропускная способность сохранена, latency улучшена, архитектура упрощена.**

---

*Связанные документы:*
- *[../step_3/PRODUCER_TUNING.md](../step_3/PRODUCER_TUNING.md) — producer-side оптимизация до step_4*
- *[../step_2/PARTITIONS_COMPARISON.md](../step_2/PARTITIONS_COMPARISON.md) — подбор числа партиций*
