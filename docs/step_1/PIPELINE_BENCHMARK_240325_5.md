# Pipeline Benchmark #5: Стресс-тест пределов системы (1 uvicorn worker)

**Date:** 25.03.2026 | **Environment:** Docker (WSL2), 1 worker uvicorn | **Tool:** k6

## Цель

Найти реальные пределы текущей конфигурации (1 uvicorn worker, 1 Kafka partition, 1 consumer). В Benchmark #4 все тесты прошли с 0% ошибок и огромным запасом — система была недогружена.

## Что изменилось vs #4

| Параметр | Benchmark #4 | Benchmark #5 | Изменение |
|----------|-------------|-------------|-----------|
| **Throughput target rate** | 5→100 req/s | 10→200 req/s | **x2** |
| **Throughput threshold p95** | <5000ms | **<500ms** | **x10 жёстче** |
| **Throughput threshold errors** | <10% | **<5%** | **x2 жёстче** |
| **Spike VUs** | 50 | **200** | **x4** |
| **Spike threshold errors** | <30% | **<10%** | **x3 жёстче** |
| **Consumer lag VUs** | 1→10 | **1→20** | **x2** |
| `stress.js` | удалён в #4 | — | — |

**Очистка перед каждым тестом:** TRUNCATE ClickHouse + пересоздание Kafka topic + restart consumer.

---

## Результаты

### Throughput — нарастающая нагрузка (10 → 200 req/s, batch/1)

| Метрика | Benchmark #4 | Benchmark #5 | Изменение |
|---------|-------------|-------------|-----------|
| Всего запросов | 2,812 | **6,965** | **x2.5** |
| RPS | 37.0 | **99.5** | **x2.7** |
| Ошибки | 0% | **0%** | = |
| Duration avg | 4.15ms | **17.37ms** | +4.2x (нагрузка выше) |
| Duration med | 3.9ms | **4.76ms** | +22% |
| Duration p95 | 5.21ms | **60.91ms** | +12x (хвост под нагрузкой) |
| Max VUs | 1 | **21** | |
| dropped_iterations | 0 | **9** | API не успевала за 200 req/s |

**Все threshold пройдены** ✓ (p95=61ms < 500ms, ошибки 0% < 5%)

#### Kafka→ClickHouse lag

| Метрика | Значение |
|---------|---------|
| `lag_duration` | 3.04s (стабилизация) |
| `lag_messages` | **0** |

**Consumer справился с 99.5 RPS** — всё доставлено до замера.

---

### Spike — 200 VU одновременно (batch/1)

| Метрика | Benchmark #4 (50 VU) | Benchmark #5 (200 VU) | Изменение |
|---------|---------------------|----------------------|-----------|
| Всего запросов | 50 | **200** | **x4** |
| Ошибки | 0% | **0%** | = |
| Duration avg | 115ms | **372.27ms** | +3.2x |
| Duration med | 117.08ms | **338.77ms** | +2.9x |
| Duration p95 | 155.18ms | **604.23ms** | +3.9x |
| Duration max | 157.89ms | **621.94ms** | +3.9x |
| Время теста | 0.2s | **0.8s** | +0.6s |

**Threshold пройден** ✓ (ошибки 0% < 10%)

**200 одновременных запросов обработаны за 0.8 секунды.** Latency выросла линейно (x4 VU → x3.9 p95), что говорит о стабильной работе без деградации.

---

### Consumer Lag — тяжёлая нагрузка (batch/1000, 1→20 VUs)

| Метрика | Benchmark #4 (10 VU) | Benchmark #5 (20 VU) | Изменение |
|---------|---------------------|---------------------|-----------|
| Всего запросов | 172 | **183** | +6% |
| Отправлено сообщений | 172,000 | **183,000** | +6% |
| RPS (сообщений/с) | 3,070 | **3,265** | +6% |
| Ошибки | 0% | **0%** | = |
| Duration avg | 1.4s | **2.63s** | +88% |
| Duration p95 | 3.9s | **7.65s** | +96% |
| Max VUs | 10 | **20** | x2 |

#### Kafka→ClickHouse lag

| Метрика | #4 | #5 |
|---------|----|----|
| `lag_duration` | 3.02s | **2.02s** |
| `lag_messages` | 0 | **0** |
| CH count при замере | 171,112 | **182,995** |
| Доставлено после нагрузки | 0 | **0** |

**Consumer при 20 VU × batch/1000:** справляется полностью. Лаг = 0. RPS вырос незначительно (+6%) — bottleneck на стороне API (1 worker), а не consumer.

---

## Сводная таблица #4 vs #5

| Метрика | #4 Throughput | #5 Throughput | #4 Spike | #5 Spike | #4 Lag | #5 Lag |
|---------|-------------|-------------|---------|---------|--------|--------|
| Запросов | 2,812 | **6,965** | 50 | **200** | 172 | 183 |
| RPS / msg/s | 37 | **99.5** | 289 | 263 | 3,070 | **3,265** |
| Ошибки | 0% | 0% | 0% | 0% | 0% | 0% |
| p95 | 5ms | **61ms** | 155ms | **604ms** | 3.9s | **7.65s** |
| Lag messages | 0 | 0 | — | — | 0 | 0 |

---

## Анализ пределов

### Что выдерживает 1 uvicorn worker

| Характеристика | Предел | Как определено |
|----------------|--------|----------------|
| **Sustained RPS (batch/1)** | **~100 req/s** | throughput тест: 99.5 RPS при 0% ошибок, 9 dropped |
| **Burst (batch/1)** | **200 VU одновременно** | spike: 0% ошибок, p95=604ms |
| **Сообщений/с (batch/1000)** | **~3,265 msg/s** | consumer_lag: 20 VU, 0% ошибок |
| **Consumer lag** | **0** | Во всех тестах consumer успевает |

### Где bottleneck

1. **API (uvicorn 1 worker)** — единственное ограничение. При 200 req/s начались dropped iterations (9 из ~7000). p95 вырос с 5ms до 61ms.
2. **Kafka** — не bottleneck. Single partition справляется с 3,265 msg/s.
3. **ClickHouse** — не bottleneck. Consumer записывает все данные в реальном времени.
4. **Consumer** — не bottleneck. Lag = 0 во всех сценариях, даже при 183K сообщений.

### Запас по threshold

| Threshold | Лимит | Факт | Запас |
|-----------|-------|------|-------|
| throughput p95 | 500ms | 61ms | **x8** |
| throughput errors | 5% | 0% | **100%** |
| spike errors | 10% | 0% | **100%** |
| consumer_lag errors | 20% | 0% | **100%** |

---

## Рекомендации: что дальше

| # | Что | Ожидаемый эффект |
|---|-----|-----------------|
| 1 | `--workers 4` в uvicorn | RPS x3-4 (~400 req/s) |
| 2 | Партиционирование Kafka (4-8 partitions) + несколько consumers | Масштабирование записи в CH |
| 3 | Увеличить throughput target до 500-1000 req/s (после п.1) | Найти предел multi-worker |

---

*Benchmark #1 (singleton sync consumer): `docs/PIPELINE_BENCHMARK_ 240326_1.md`*
*Benchmark #2 (async consumer container): `docs/PIPELINE_BENCHMARK_240326_2.md`*
*Benchmark #3 (per-request sync consumer): `docs/PIPELINE_BENCHMARK_240326_3.md`*
*Benchmark #4 (async + lag monitoring): `docs/PIPELINE_BENCHMARK_240325_4.md`*
