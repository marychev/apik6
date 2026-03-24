# Pipeline Benchmark #3: FastAPI → Kafka → ClickHouse (Sync Consumer как задача)

**Date:** 24.03.2026 | **Environment:** Docker (WSL2), 1 worker uvicorn | **Tool:** k6

## Архитектура

**Consumer вызывается как задача внутри HTTP-запроса** — аналог Benchmark #1, но с рефакторингом: логика consumer вынесена в отдельную функцию `consumer_users_batch_to_clickhouse()`.

```
k6 (load) → POST /users/batch/{n}
               ↓
          [API контейнер]
               ↓
         1. prepare_user() × N        ← подготовка данных
               ↓
         2. send_users_batch(users)    ← Kafka Producer
               ↓
         3. consumer_users_batch_to_clickhouse()  ← синхронный consumer
               ↓
         poll() Kafka → batch INSERT ClickHouse
               ↓
         return {sent: N, saved_to_clickhouse: M}
```

**Отличие от #1:** Код чище (разделение ответственности), но архитектура та же — каждый HTTP-запрос ждёт полный цикл Kafka → ClickHouse.

---

## Результаты

### Throughput — нарастающая нагрузка (5 → 100 req/s)

| Метрика | Benchmark #1 | Benchmark #3 | Benchmark #2 (async) |
|---------|-------------|-------------|---------------------|
| Всего запросов | 691 | **476** | 2812 |
| RPS | 6.9 | **4.4** | 37.8 |
| Ошибки | 35.4% | **16.2%** | 0% |
| Duration avg | 14.44s | **32.53s** | 9.28ms |
| Duration med | 109ms | **35.24s** | 6ms |
| Duration p95 | 43.84s | **60s** | 25ms |
| Max VUs | 200 | **200** | 2 |

**Все 4 threshold провалены** (как и в #1).

### Stress — нарастающие VUs (1 → 20)

| Метрика | Benchmark #1 | Benchmark #3 | Benchmark #2 (async) |
|---------|-------------|-------------|---------------------|
| Всего запросов | 252 | **75** | 27,908 |
| RPS | 3.5 | **0.76** | 429 |
| Ошибки | 39.7% | **13.3%** | 0% |
| Duration avg | 2.89s | **8.77s** | 21.87ms |
| Duration med | 163ms | **10.02s** | 18ms |
| Duration p95 | 10.97s | **15.33s** | 43ms |
| Отправлено | 152 | **65** | 27,908 |
| Сохранено | 150 | **43** | — (async) |
| Потери | 1.3% | **33.8%** | 0% |

**http_req_duration threshold провален** (в #1 — http_req_failed провален).

### Spike — 50 VU одновременно

| Метрика | Benchmark #1 | Benchmark #3 | Benchmark #2 (async) |
|---------|-------------|-------------|---------------------|
| Всего запросов | 50 | **50** | 50 |
| Ошибки | 8% | **56%** | 0% |
| Duration avg | 10.53s | **5.51s** | 156ms |
| Duration med | 10.22s | **402ms** | 153ms |
| Duration p95 | 20.19s | **12.16s** | 223ms |
| Отправлено | 46 | **22** | 50 |
| Сохранено | 39 | **0** | — (async) |
| Потери | 15.2% | **100%** | 0% |

**http_req_failed threshold провален** — 56% ошибок. Из 22 успешных запросов — 0 сохранено в ClickHouse (consumer не успел вычитать данные из Kafka за время poll).

---

## Сводная таблица всех бенчмарков

| Метрика | #1 Throughput | #3 Throughput | #2 Throughput | #1 Stress | #3 Stress | #2 Stress | #1 Spike | #3 Spike | #2 Spike |
|---------|-------------|-------------|-------------|----------|----------|----------|---------|---------|---------|
| Запросов | 691 | 476 | **2,812** | 252 | 75 | **27,908** | 50 | 50 | 50 |
| RPS | 6.9 | 4.4 | **37.8** | 3.5 | 0.76 | **429** | 2.5 | 4.1 | **219** |
| Ошибки | 35.4% | 16.2% | **0%** | 39.7% | 13.3% | **0%** | 8% | 56% | **0%** |
| p95 | 43.84s | 60s | **25ms** | 10.97s | 15.33s | **43ms** | 20.19s | 12.16s | **223ms** |

---

## Проверка данных

```bash
$ docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM users"
4603
```

Отправлено за все тесты #3: ~486 (399 + 65 + 22). В ClickHouse: 4,603 (включая накопленные данные от предыдущих тестов).

---

## Сравнение #3 vs #1

| | #1 (старый sync) | #3 (новый sync) | Причина разницы |
|---|---|---|---|
| Ошибки (throughput) | 35.4% | 16.2% | Новый consumer создаётся на каждый запрос → нет конкуренции за singleton |
| RPS (stress) | 3.5 | 0.76 | Consumer.close() на каждый запрос — оверхед на group rejoin |
| Потери (spike) | 15.2% | 100% | Новый consumer не успевает получить partition assignment за poll timeout |
| p95 (throughput) | 43.84s | 60s | Те же блокировки + оверхед на создание/закрытие consumer |

**Вывод:** Benchmark #3 подтверждает, что синхронный consumer — фундаментальная проблема, а не вопрос качества кода. Рефакторинг не улучшил производительность. Создание нового consumer на каждый запрос даже хуже singleton-подхода (#1).

---

## Выводы

1. **Синхронный consumer в любой форме — бутылочное горлышко.** Неважно, singleton (#1) или per-request (#3) — API зависит от скорости Kafka poll + ClickHouse INSERT.

2. **Per-request consumer хуже singleton:** оверхед на group join/leave + partition assignment при каждом запросе. Spike-тест: 100% потерь vs 15.2% в #1.

3. **Асинхронный consumer (#2) — единственный вариант** для production: RPS x86 (0.76 → 429), 0% ошибок, p95 43ms vs 15s.

4. **Порядок от худшего к лучшему:** #3 (per-request sync) < #1 (singleton sync) << #2 (async container).

---

*Benchmark #1 (singleton sync consumer): `docs/PIPELINE_BENCHMARK_ 240326_1.md`*
*Benchmark #2 (async consumer container): `docs/PIPELINE_BENCHMARK_240326_2.md`*
