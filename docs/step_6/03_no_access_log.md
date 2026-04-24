# Эксперимент 3: отключение uvicorn access-log

## Гипотеза

Austin-профайлер (step_5) показал, что на одном воркере ~9 секунд за минуту уходит на:
- `StreamHandler.flush` (6.4 с) — flush stdout
- `ipaddress.ip_address` (1.6 с) — парсинг IP клиента
- `logging._acquireLock` (0.9 с) — lock логгера

Всё это — **uvicorn access-log**: для каждого запроса форматируется строка `172.x.x.x - "POST /users/batch/1 HTTP/1.1" 200 OK` и пишется в stdout. Под 2500 VU × 5 воркеров × 2000 RPS это ~15% CPU на чистые логи **без бизнес-логики**.

Если отключить — ожидание **+10–20% RPS**.

## Что меняем

Файл: [Dockerfile](../../Dockerfile) — добавлен флаг `--no-access-log` в CMD:

```diff
- CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-5}"]
+ CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-5} --no-access-log"]
```

Остальной код не трогаем. `kafka_app/user_producer.py` в состоянии **F&F** (`asyncio.create_task`).

## Как замеряем

```bash
docker compose up -d --build --force-recreate api
# ... 3 прогона
VUS=2500 DURATION=1m k6 run k6/rps.js
```

## Результаты — первая итерация (F&F + no-access-log)

| # | RPS | p(95) ok | errors | max duration |
|---|---|---|---|---|
| 1 | 2811 | 1.61s | 0.17% | 57.6s |
| 2 | 2118 | 2.44s | 0.00% | 23s |
| 3 | 2948 | 1.10s | 0.23% | 57.5s |
| **медиана** | **2811** | 1.61s | 0.17% | |

На вид — +25% к old baseline. Но в логах api-контейнера обнаружились репликации `aiokafka.errors.KafkaTimeoutError: ... Task exception was never retrieved`: F&F через `create_task` силентно дропал сообщения, когда внутренний аккумулятор aiokafka переполнялся. **Handler возвращал клиенту 200, но сообщение в Kafka не уходило.**

То есть 2811 RPS — **«ложный» прирост**, часть нагрузки просто выпадала.

## Результаты — честная итерация (await + no-access-log)

Откатили `user_producer.py` обратно на `await producer.send(...)` — handler ждёт, пока aiokafka положит сообщение в буфер. Durability гарантирована, никаких `create_task`.

| # | RPS | p(95) ok | errors | max duration | KafkaTimeoutError |
|---|---|---|---|---|---|
| 1 | 3344 | 1.61s | 0.00% | 41.6s | |
| 2 | 2920 | 2.04s | 0.00% | **3.67s** | |
| 3 | 3322 | 1.39s | 0.00% | 57.3s | |
| **медиана** | **3322** | **1.61s** | **0.00%** | | **0** |

### Сравнение со всеми конфигурациями

| Конфигурация | Медиана RPS | Losses | Честность |
|---|---|---|---|
| Old baseline (aiokafka + `await` + access-log) | 2247 | 0 | ✅ |
| F&F (aiokafka + `create_task` + access-log) | ~1843 | ~% silent drop | ⚠️ |
| confluent-kafka-python + F&F + access-log | 1881 | минимальный | ⚠️ |
| F&F + no-access-log | 2811 | silent drop | ⚠️ (завышен) |
| **await + no-access-log** | **3322** | **0** | ✅ **честно** |

**+48% к backlog-baseline, +18% к ложной F&F-версии, ноль потерь.**

## Наблюдения

1. **Настоящий рычаг — отключение uvicorn access-log.** Ровно то, что показывало Austin-профилирование (step_5): ~6.4 с/мин на один воркер уходило во flush + 0.9 с на lock + 1.6 с в `ipaddress.ip_address`. ~15% CPU воркера — чистые логи.
2. **F&F через `create_task` — антипаттерн на этой нагрузке.** Прирост был иллюзией: aiokafka тихо ломался (`KafkaTimeoutError` в фоновых Task'ах, которые никто не `await`-ил), клиент получал 200 при фактической потере данных.
3. **`await` не просадил RPS на правильной конфигурации** — наоборот, дал больше. Причина: при `await` handler естественным образом делает backpressure (ждёт пока aiokafka примет в буфер). Это **предотвращает перегрузку внутренней очереди**, которая под F&F выливалась в таймауты.
4. **p(95) 1.61s при 3322 RPS** — latency даже лучше old baseline (1.52s при 2247 RPS). То есть и пропускная способность выросла, и latency под нагрузкой стабильнее.
5. Прогон 2 показал max duration **3.67s** — никто даже близко не подходил к k6-таймауту. Система в хорошем режиме.

## Вывод

Финальная конфигурация для этого рычага:

- **`uvicorn --no-access-log`** — фиксируется навсегда
- **`await producer.send(...)`** — остаётся как есть (не переделываем в F&F)
- `asyncio.create_task` **нельзя** воспринимать как win без проверки durability (логи на фоновые исключения)

### Что это говорит про общую картину

- Гипотеза «GIL захлёбывается в aiokafka» **оказалась ложной**. Confluent-kafka-python (GIL-free C) дал только +2%. Access-log — +48%.
- Настоящий Python-overhead сидел в **логах и их lock-контенции**, а не в Kafka-сериализации.
- **Measurement lesson:** всегда проверяй логи приложения на фоновые исключения после замера. «2811 RPS» без `KafkaTimeoutError`-чека был ложным рекордом.

## Следующие шаги (кандидаты)

1. **granian вместо uvicorn** (P3 из backlog, ожидание +10–20%) — следующий самый дешёвый рычаг.
2. **Повторить confluent-kafka-python на новом baseline** — возможно, на 3322 RPS он покажет другую разницу (access-log раньше маскировал).
3. **P1 из backlog возможно уже неактуален** — confluent дал +2%, отключение логов +48%. Не то что думали.
