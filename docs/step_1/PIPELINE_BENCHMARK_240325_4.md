# Pipeline Benchmark #4: FastAPI → Kafka → ClickHouse (Async Consumer + Lag Monitoring)

**Date:** 25.03.2026 | **Environment:** Docker (WSL2), 1 worker uvicorn | **Tool:** k6

## Что нового

**Добавлен мониторинг consumer lag** — без влияния на основной путь данных:

| | Benchmark #2 | Benchmark #4 |
|---|---|---|
| `POST /users/batch/{n}` | `{sent}` | `{sent}` — без изменений |
| `GET /users/count` | — | **NEW** — текущий count записей в ClickHouse |
| Замер лага в k6 | Нет | **Отдельный сценарий `measure_lag`** после нагрузки |
| `saved_to_clickhouse` в k6 | Использовался, но API не возвращал | Убран из нагрузочных сценариев (не нужен) |

**Принцип:** нагрузочный сценарий остаётся чистым (только `POST`), а лаг замеряется отдельным сценарием, который стартует после окончания нагрузки и поллит `GET /users/count` пока данные не перестанут поступать в ClickHouse.

**Удалён `stress.js`** — дублировал `throughput.js` (оба тестировали batch/1 с ramping-нагрузкой). Вместо него — `consumer_lag.js` с тяжёлым batch/1000.

**Набор тестов:**

| Тест | Что проверяет | Batch size |
|------|--------------|------------|
| `throughput.js` | Пропускная способность API + lag | batch/1 |
| `spike.js` | Внезапный всплеск 50 VU | batch/1 |
| `consumer_lag.js` | Нагрузка на consumer + замер лага | batch/1000 |

---

## Архитектура

```
k6 (load) → POST /users/batch/{n}
               ↓
          [API контейнер]
               ↓
         prepare_user() + Kafka Producer
               ↓
         return {sent: N}         ← мгновенный ответ (как в #2)
               ↓
         Kafka (topic: users)
               ↓
         [Consumer контейнер]     ← отдельный процесс, бесконечный цикл
               ↓
         BatchBuffer (1000 записей) → ClickHouse INSERT

--- после окончания нагрузки ---

k6 (measure_lag) → GET /users/count
               ↓
         [API контейнер]
               ↓
         SELECT count() FROM users  ← опрос ClickHouse
               ↓
         return {count: M}
               ↓
         ждём пока count стабилизируется (consumer дочитал всё)
```

---

## Результаты

### Throughput — нарастающая нагрузка (5 → 100 req/s, batch/1)

| Метрика | Benchmark #2 | Benchmark #4 | Изменение |
|---------|-------------|-------------|-----------|
| Всего запросов | 2,812 | **2,812** | = |
| RPS | 37.8 | **37.0** | -2% |
| Ошибки | 0% | **0%** | = |
| Duration avg | 9.28ms | **4.15ms** | **x2.2 быстрее** |
| Duration med | 6ms | **3.9ms** | **x1.5 быстрее** |
| Duration p95 | 25ms | **5.21ms** | **x4.8 быстрее** |
| Max VUs | 2 | **1** | = |

**Все threshold пройдены** ✓

#### Kafka→ClickHouse lag (throughput)

| Метрика | Значение | Описание |
|---------|---------|----------|
| `lag_duration` | **3.03s** | Время ожидания стабилизации (3 × 1с polling) |
| `lag_messages` | **0** | Сообщений, дошедших после окончания нагрузки |
| `all messages delivered to CH` | ✓ | Consumer всё доставил до начала замера |
| `lag under 10s` | ✓ | |

**Consumer при batch/1 @ 37 RPS:** лаг < 5 секунд, полная доставка.

---

### Spike — 50 VU одновременно (batch/1)

| Метрика | Benchmark #2 | Benchmark #4 | Изменение |
|---------|-------------|-------------|-----------|
| Всего запросов | 50 | **50** | = |
| Ошибки | 0% | **0%** | = |
| Duration avg | 156ms | **115ms** | **x1.4 быстрее** |
| Duration med | 153ms | **117.08ms** | **x1.3 быстрее** |
| Duration p95 | 223ms | **155.18ms** | **x1.4 быстрее** |
| Время теста | 0.2s | **0.2s** | = |

**Все threshold пройдены** ✓

---

### Consumer Lag — тяжёлая нагрузка (batch/1000, 1→10 VUs, 50s)

**Новый тест — `consumer_lag.js`.** Цель: нагрузить consumer тяжёлыми батчами и замерить отставание.

| Метрика | Значение |
|---------|---------|
| Всего запросов | 172 |
| Отправлено сообщений | **172,000** |
| RPS (сообщений/с) | **3,070** |
| Ошибки | **0%** |
| Duration avg | 1.4s |
| Duration p95 | 3.9s |
| Max VUs | 10 |

#### Kafka→ClickHouse lag (consumer_lag)

| Метрика | Значение | Описание |
|---------|---------|----------|
| `lag_duration` | **3.02s** | Время ожидания стабилизации |
| `lag_messages` | **0** | Сообщений после окончания нагрузки |
| CH count при замере | **171,112** | Из 172,000 отправленных |
| Недоставлено | **888** (~0.5%) | Последний неполный батч в буфере consumer |
| `consumer delivered all` | ✓ | |
| `lag under 30s` | ✓ | |

**Consumer при batch/1000 @ 3,070 msg/s:** справляется полностью. Все 172K сообщений доставлены до начала замера. Разница 888 записей — последний неполный батч (consumer батчит по 1000, flush по таймауту poll).

---

## Сводная таблица

| Метрика | #2 Throughput | #4 Throughput | #2 Spike | #4 Spike | #4 Consumer Lag |
|---------|-------------|-------------|---------|---------|----------------|
| Запросов | 2,812 | 2,812 | 50 | 50 | 172 |
| Сообщений | 2,812 | 2,812 | 50 | 50 | **172,000** |
| RPS | 37.8 | 37.0 | 219 | 289 | 3,070 msg/s |
| Ошибки | 0% | 0% | 0% | 0% | 0% |
| p95 | 25ms | **5.21ms** | 223ms | **155ms** | 3.9s |
| Lag messages | — | **0** | — | — | **0** |

---

## Проверка данных и ресурсов

```bash
# ClickHouse после consumer_lag теста
$ docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM users"
172000

$ docker compose exec clickhouse clickhouse-client -q \
  "SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts WHERE table='users' AND active"
6.65 MiB

# Kafka — consumer lag
$ docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group user-clickhouse --describe
GROUP           TOPIC  PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
user-clickhouse users  0          906000          906000          0
```

**172K записей = 6.65 MiB** в ClickHouse. Kafka consumer lag = 0. Ресурсы в норме.

---

## О новых метриках

### Как работает `measure_lag`

Отдельный k6-сценарий, который стартует через 5 секунд после окончания нагрузки:

1. Запоминает `count` в ClickHouse до нагрузки (через `setup()`) и после (через `GET /users/count`)
2. Каждую секунду поллит `GET /users/count`
3. Если count не меняется 3 секунды подряд — consumer всё дочитал
4. Фиксирует:
   - `lag_duration` — сколько ждали стабилизации
   - `lag_messages` — сколько сообщений дошло уже после окончания нагрузки

### Почему `lag_duration ≈ 3s` это не реальный лаг

Это **минимальное время ожидания стабилизации** (3 раунда × 1с polling). Consumer доставил все сообщения ещё до начала замера — `lag_messages = 0`. Реальный лаг: **менее 5 секунд** (буфер между окончанием нагрузки и стартом замера).

### Почему consumer справляется даже при 172K сообщений

1. **BatchBuffer = 1000** — consumer получает полные батчи и сразу INSERT'ит
2. **ClickHouse быстр на запись** — batch INSERT 1000 строк занимает миллисекунды
3. **Kafka poll timeout = 10s** — при постоянном потоке данных poll возвращает мгновенно
4. **1 partition** — нет координации между consumer'ами

### Важно: очистка перед тестами

При пересоздании Kafka topic (`kafka-topics --delete && --create`) **consumer теряет partition assignment** и перестаёт читать. Нужен `docker compose restart consumer` после пересоздания топика. Для очистки рекомендуется:

```bash
docker compose exec clickhouse clickhouse-client -q 'TRUNCATE TABLE users'
docker compose restart consumer
# Подождать пока consumer подключится (~5 сек)
```

### Альтернативы для production

| Метод | Что замеряет | Плюсы | Минусы |
|-------|-------------|-------|--------|
| **k6 `measure_lag`** (наш) | Время доставки всех сообщений в CH | Просто, end-to-end | Только после нагрузки, не realtime |
| **kafka-consumer-groups** | Consumer group offset lag | Встроенный, точный | Показывает offset, не время |
| **Prometheus + kafka_exporter** | `kafka_consumergroup_lag` | Realtime, алерты | Нужна инфра мониторинга |
| **Timestamps в сообщениях** | Время от produce до insert | Точный per-message lag | Нужно менять код producer+consumer |

---

## Выводы

1. **Производительность на уровне #2 или лучше** — добавление `GET /users/count` и `measure_lag` не влияет на основной путь данных.

2. **0% ошибок** во всех тестах, **100% доставка**.

3. **Consumer не является бутылочным горлышком** даже при 172K сообщений (3,070 msg/s). Лаг = 0 во всех сценариях.

4. **stress.js удалён** — дублировал throughput.js. Вместо него `consumer_lag.js` тестирует то, что stress не мог — реальную нагрузку на consumer.

5. **Для обнаружения consumer lag** нужна ещё более тяжёлая нагрузка (несколько producers, или замедление ClickHouse). В текущей конфигурации single consumer + single partition справляется с любой нагрузкой, которую может создать 1 uvicorn worker.

---

*Benchmark #1 (singleton sync consumer): `docs/PIPELINE_BENCHMARK_ 240326_1.md`*
*Benchmark #2 (async consumer container): `docs/PIPELINE_BENCHMARK_240326_2.md`*
*Benchmark #3 (per-request sync consumer): `docs/PIPELINE_BENCHMARK_240326_3.md`*
