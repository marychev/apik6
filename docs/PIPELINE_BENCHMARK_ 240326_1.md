# Pipeline Benchmark: FastAPI → Kafka → ClickHouse

**Date:** 24.03.2026 | **Environment:** Docker (WSL2), 1 worker uvicorn | **Tool:** k6

Нагрузочное тестирование пайплайна создания пользователей. Один запрос `POST /users/batch/1` проходит полный цикл: подготовка данных → отправка в Kafka → чтение из Kafka → запись в ClickHouse.

---

## 1. Архитектура

```
k6 (load) → POST /users/batch/{n}
               ↓
          [FastAPI API]
               ↓
         prepare_user()          ← генерация UUID + Pydantic
               ↓
         Kafka Producer          ← send() + flush()
               ↓
         Kafka (topic: users)
               ↓
         Kafka Consumer          ← poll() в том же запросе
               ↓
         ClickHouse INSERT       ← clickhouse-connect batch insert
               ↓
         Response: {sent, saved_to_clickhouse}
```

Особенность: consumer вызывается **синхронно внутри HTTP-запроса** (не фоновый процесс). Это даёт точное измерение полного цикла, но ограничивает throughput.

---

## 2. Методология

### Что измеряли

| Метрика | Описание |
|---------|----------|
| **RPS** | Запросов в секунду (iterations/s) |
| **batch_duration** | Полное время запроса: prepare → Kafka → ClickHouse |
| **kafka_lag** | Оценка лага доставки Kafka → ClickHouse |
| **lost_messages** | Потерянные сообщения (sent - saved_to_clickhouse) |
| **http_req_failed** | Процент ошибок |

### Тесты

| Тест | Команда | Сценарий |
|------|---------|----------|
| Throughput | `make k6-throughput` | Нарастающая нагрузка 5 → 100 req/s, 70 сек |
| Stress | `make k6-stress` | Ramping VUs 1 → 20, каждый batch/1, 60 сек |
| Spike | `make k6-spike` | 50 VU одновременно, 50 итераций batch/1 |

---

## 3. Результаты

### Throughput — нарастающая нагрузка (5 → 100 req/s)

| Метрика | Значение |
|---------|----------|
| Всего запросов | 691 |
| RPS | 6.9 req/s |
| Успешных | 64.6% (446 из 691) |
| Ошибок | 35.4% |
| batch_duration avg | 14.44s |
| batch_duration med | 109ms |
| batch_duration p95 | **43.84s** |
| kafka_lag p95 | 45.55s |
| Отправлено в Kafka | 446 |
| Сохранено в ClickHouse | 391 |
| Потери | **12.3%** (55 записей) |

**Вывод:** Система стабильна при ~10 req/s. При нарастании до 30+ req/s — деградация: запросы начинают копиться (200 VUs в очереди), p95 растёт до 44 сек. Consumer внутри запроса блокирует поток — это основное бутылочное горлышко.

### Stress — нарастающие VUs (1 → 20)

| Метрика | Значение |
|---------|----------|
| Всего запросов | 252 |
| RPS | 3.5 req/s |
| Успешных | 60.3% (152 из 252) |
| Ошибок | 39.7% |
| batch_duration avg | 2.89s |
| batch_duration med | 163ms |
| batch_duration p95 | **10.97s** |
| Отправлено в Kafka | 152 |
| Сохранено в ClickHouse | 150 |
| Потери | **1.3%** (2 записи) |

**Вывод:** При 5-10 VUs система работает стабильно (med 163ms). При 15+ VUs появляются EOF-ошибки — uvicorn (1 worker) не успевает принять подключения. Потери данных минимальны.

### Spike — 50 VU одновременно

| Метрика | Значение |
|---------|----------|
| Всего запросов | 50 |
| Успешных | 92% (46 из 50) |
| Ошибок | 8% (4 запроса) |
| http_req_duration avg | **10.53s** |
| http_req_duration med | 10.22s |
| http_req_duration p95 | **20.19s** |
| Отправлено в Kafka | 46 |
| Сохранено в ClickHouse | 39 |
| Потери | **15.2%** (7 записей) |

**Вывод:** При резком всплеске 50 VU — основная масса запросов обрабатывается за 10-12 сек. 4 запроса не дошли до API. 15% потерь на этапе Kafka → ClickHouse (consumer timeout при конкуренции за poll).

---

## 4. Сводная таблица

| Метрика | Throughput | Stress | Spike |
|---------|-----------|--------|-------|
| Запросов | 691 | 252 | 50 |
| RPS | 6.9 | 3.5 | 2.5 |
| Ошибки | 35.4% | 39.7% | 8% |
| Duration avg | 14.44s | 2.89s | 10.53s |
| Duration med | 109ms | 163ms | 10.22s |
| Duration p95 | 43.84s | 10.97s | 20.19s |
| Sent → Saved | 446 → 391 | 152 → 150 | 46 → 39 |
| Потери | 12.3% | 1.3% | 15.2% |

---

## 5. Проверка данных

```bash
$ docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM users"
3825
```

Данные доставлены. Часть потерь связана с consumer timeout при конкурентном poll() — несколько VU пытаются читать из одного consumer group одновременно.

---

## 6. Узкие места и выводы

### Бутылочные горлышки

1. **Синхронный consumer внутри HTTP-запроса** — блокирует ответ на время poll(). При 50 VU каждый ждёт своей очереди на consumer.
2. **Один worker uvicorn** — при 15+ одновременных подключений начинаются EOF (отказ в обслуживании).
3. **Общий KafkaConsumer (singleton)** — при конкуренции VUs теряются сообщения (один poll() забирает данные другого VU).

### Что работает хорошо

- **Kafka Producer** — отправка стабильна, потерь на этапе produce нет.
- **ClickHouse INSERT** — при доставке данных запись быстрая, без ошибок.
- **Медианное время** при низкой нагрузке: **109-163ms** — приемлемо для полного цикла.

### Рекомендации по оптимизации

| # | Что | Ожидаемый эффект |
|---|-----|-----------------|
| 1 | Увеличить uvicorn workers (`--workers 4`) | x3-4 RPS, меньше EOF |
| 2 | Вынести consumer в фоновый процесс | API отвечает мгновенно, лаг асинхронный |
| 3 | Consumer с BatchBuffer (накопление + bulk insert) | Меньше нагрузка на ClickHouse |
| 4 | Отдельный consumer group per VU или партиционирование | Устранение конкуренции за poll() |

---

## 7. Инфраструктура

| Сервис | Образ | Порт |
|--------|-------|------|
| API | python:3.12-slim + FastAPI | 8000 |
| Kafka | confluentinc/cp-kafka:7.5.0 | 9092 (internal), 9093 (external) |
| Zookeeper | confluentinc/cp-zookeeper:latest | 2181 |
| ClickHouse | clickhouse/clickhouse-server:latest | 8123 (HTTP), 9000 (native) |

---

*Тесты прогнаны 24.03.2026, k6 v0.x, Docker Desktop WSL2*
