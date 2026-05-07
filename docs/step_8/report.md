# Step 8 — Отчёт о тюнинге .env параметров

**Дата:** 2026-05-07 — 2026-05-08
**Железо:** Intel i3-1005G1 (2 ядра / 4 потока), 8 GB RAM
**Стек:** FastAPI + aiokafka, uvicorn, Kafka (Confluent 7.5.0), без ClickHouse
**Нагрузка:** k6, VUS=2500, длительность 1m, эндпоинт `POST /users/batch/1`
**Бейзлайн (start step_8):** 1392 RPS (UVICORN_WORKERS=1)
**Лучший результат:** **4097 RPS** (+194% к бейзлайну)

---

## Сводка по запускам (best-of-N)

| #    | Конфигурация                                                                 | best RPS | p95     |
|------|------------------------------------------------------------------------------|----------|---------|
| I    | workers=1, default kafka                                                     | 1 392    | 2.24s   |
| II   | workers=2                                                                    | 2 827    | 1.39s   |
| III  | workers=3                                                                    | 3 244    | 1.25s   |
| IV   | workers=4                                                                    | 3 467    | 1.31s   |
| V    | workers=5                                                                    | 3 458    | 1.40s   |
| VI   | workers=6                                                                    | 3 320    | 1.50s   |
| VII  | workers=4, partitions=2                                                      | 3 729    | 1.00s   |
| VIII | workers=5, partitions=2                                                      | 3 761    | 1.24s   |
| IX   | workers=4, partitions=3                                                      | 3 873    | 1.16s   |
| X    | workers=5, partitions=3                                                      | 3 857    | 1.38s   |
| XI   | workers=5, partitions=3, net/io threads=3                                    | 3 888    | 1.39s   |
| XII  | **workers=4, partitions=4, linger=50, batch=256KB, net=2/io=4**              | **4 097**| **1.15s** |
| XIII | XII + linger=100, batch=512KB                                                | 3 945    | 1.03s   |

---

## Лучшая конфигурация

```env
UVICORN_WORKERS=4

KAFKA_NUM_PARTITIONS=4

KAFKA_ENGINE_NUM_CONSUMERS=4
KAFKA_ENGINE_POLL_TIMEOUT_MS=500
KAFKA_ENGINE_POLL_MAX_BATCH_SIZE=500000
KAFKA_ENGINE_FLUSH_INTERVAL_MS=7500

KAFKA_PRODUCER_LINGER_MS=50
KAFKA_PRODUCER_BATCH_SIZE=262144
KAFKA_PRODUCER_COMPRESSION=lz4
KAFKA_PRODUCER_ACKS=1
KAFKA_PRODUCER_IDEMPOTENT=false

KAFKA_NUM_NETWORK_THREADS=2
KAFKA_NUM_IO_THREADS=4
```

---

## Ключевые выводы

| параметр | оптимум | замечание |
|---|---|---|
| **UVICORN_WORKERS** | 4 | sweet spot на 2 ядрах. 1→4 даёт основной прирост (+150%). 5–6 уже ухудшают (context-switch) |
| **KAFKA_NUM_PARTITIONS** | 4 | каждое увеличение давало +5–10% RPS. Кратность к workers/consumers важна |
| **KAFKA_PRODUCER_LINGER_MS** | 50 | 100 уже даёт хуже — слишком долго копит батчи при текущем RPS |
| **KAFKA_PRODUCER_BATCH_SIZE** | 262144 (256KB) | 512KB не помог — батчи и так не наполняются |
| **KAFKA_PRODUCER_COMPRESSION** | lz4 | оставлен, лучший баланс CPU/сети |
| **KAFKA_PRODUCER_ACKS** | 1 | компромисс надёжность/скорость |
| **NET_THREADS / IO_THREADS** | 2 / 4 | на 2 ядрах больше потоков лишь конкурируют за CPU |

## Замечания и провалы

- **ACKS=0 + COMPRESSION=none** — попытка дать +20% RPS провалилась: aiokafka не принимает строку `"none"` (нужен Python `None` или допустимый алгоритм). Контейнер не стартовал.
- **6 воркеров на 2 ядрах** — деградация до 3 130 RPS, явный потолок CPU.
- **Connection reset by peer** появлялся при слишком агрессивных конфигах (большие батчи + heap), что указывает на близость к лимитам ресурсов WSL.

## Что дальше

1. Включить ClickHouse и измерить consumer-side (`KAFKA_ENGINE_*` сейчас не нагружены).
2. Профилировать api: где именно идёт CPU — в FastAPI/uvicorn или в aiokafka сериализации.
3. Попробовать `acks=0` корректно (либо допустимое значение, либо допилить `producer.py` для конвертации `"none"`→`None`).
4. Попробовать `KAFKA_HEAP_OPTS=-Xmx1G` для брокера + мониторить swap WSL.
5. Перейти от .env к коду: `max_in_flight_requests_per_connection`, `buffer_memory` aiokafka, кастомный сериализатор.

---

## Метрика прогресса

```
step_5 → step_6:    2247 → 3322 RPS  (+48%, uvicorn --no-access-log)
step_7 → step_8:    3322 → 4097 RPS  (+23%, тюнинг workers + kafka params)
итого с baseline:   1392 → 4097 RPS  (+194%)
```
