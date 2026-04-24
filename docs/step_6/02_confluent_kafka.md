# Эксперимент 2: confluent-kafka-python (librdkafka)

## Гипотеза

Оставшийся разрыв Python ↔ Go (x3.47) сидит не во FastAPI/Pydantic (Starlette-тест показал ~20% франшизы), а в **aiokafka** — Python-имплементации Kafka-протокола. Вся сериализация, CRC, compression, partitioning — Python под GIL, серилизовано в рамках одного воркера.

`confluent-kafka-python` — тонкая обёртка над **librdkafka** (C). Ожидаемые эффекты:
- **GIL отпускается** во время `produce()` — другие корутины того же воркера работают параллельно
- Background C-thread шлёт в Kafka — Python-поток свободен
- Сериализация/compression/CRC в C

Backlog prior expectation: **+30–80% RPS**.

## Что меняем

Новое приложение в [app_confluent/](../../app_confluent/) — параллельно baseline (не ломает `make up`).

**Идентично baseline:**
- FastAPI + Pydantic v2 + orjson
- `linger_ms=20, batch_size=64KB, lz4, acks=1` (то же что aiokafka config)
- Тот же endpoint `POST /users/batch/{n}`
- uvicorn с тем же `--workers`

**Отличается:**
- `confluent_kafka.Producer` вместо `aiokafka.AIOKafkaProducer`
- `producer.produce()` **синхронный не-блокирующий** — кладёт в C-очередь librdkafka, возвращается сразу. Нет `await`, нет `create_task`.
- Фоновая задача `_poll_loop` раз в 100 мс вызывает `poll(0)` — разгребает delivery-queue librdkafka.
- orjson-сериализация вызывается inline в handler'е (librdkafka ждёт `bytes`, а не Python dict)

## Как запускать

```bash
cd /home/apik6

# Поднять confluent-прототип (baseline при этом может крутиться параллельно — он на 8000, confluent на 8003)
docker compose --profile confluent up -d --build api_confluent

# Убедиться что поднялось
docker compose ps

# Смоук
curl -X POST http://localhost:8003/users/batch/1

# k6 с кастомным URL
BASE_URL=http://localhost:8003 VUS=2500 DURATION=1m k6 run k6/rps.js
```

## Как замеряем

Три прогона k6 подряд. Сравниваем **медиану** с today-baseline (не с 2247 из backlog — тот устарел, по нашим недавним замерам сегодня воркер даёт ~1700–2000 RPS).

Если хочется сделать чистый A/B:
1. 3 прогона baseline на `localhost:8000` (основной api)
2. 3 прогона confluent на `localhost:8003`
3. Оба стека в одной сессии, одинаковая нагрузка на WSL → честное сравнение

## Результаты

Эксперимент прошёл **в две итерации**.

### Итерация 1 — с uvicorn access-log (шумная)

Первоначальный confluent-прототип не имел `--no-access-log`, и baseline (на :8000) тоже был с access-log. Получили:

| Стек | Медиана RPS | p(95) |
|---|---|---|
| baseline (aiokafka + F&F + access-log) | ~1843 | ~2.1s |
| confluent + F&F + access-log | **1881** | 2.02s |

Δ = +2%, в пределах шума. Вывод казался — «confluent ничего не даёт».

**Но:** в этот момент мы ещё не знали про `--no-access-log` как главный рычаг. Access-log маскировал ~15% CPU воркера, и любой выигрыш в Kafka-слое терялся в логах. Плюс F&F силентно дропал сообщения (см. [03_no_access_log.md](03_no_access_log.md)).

### Итерация 2 — на честном baseline (оба с `--no-access-log`, оба с `await`)

После того как установили, что настоящий рычаг — отключение access-log и возврат к `await`, повторили сравнение в чистых условиях:

| Стек | # 1 | # 2 | # 3 | **медиана RPS** | **медиана p(95)** | errors |
|---|---|---|---|---|---|---|
| aiokafka + await + no-access-log | 3344 | 2920 | 3322 | **3322** | 1.61s | 0.00% |
| confluent + await + no-access-log | 2988 | 3315 | 3127 | **3127** | **1.26s** | 0.00% |

### Сравнение медиан

| Метрика | aiokafka | confluent | Δ |
|---|---|---|---|
| RPS | 3322 | 3127 | **−6%** |
| p(95) | 1.61s | 1.26s | **−22%** (лучше) |
| errors | 0.00% | 0.00% | — |
| delivery losses (KafkaTimeoutError) | 0 | 0 | — |

## Наблюдения

1. **Гипотеза про +30–80% полностью опровергнута.** Confluent не даёт буста по RPS, даже проигрывает aiokafka на 6%. GIL-free send не помогает, когда GIL уже освободил access-log.
2. **Confluent улучшает p(95) на 22%** — хвост задержек реально лучше. librdkafka C-thread отправляет в Kafka параллельно с Python-обработкой, каждый отдельный request завершается быстрее.
3. **Просадка по RPS у confluent** — скорее всего из-за фонового `_poll_loop` (корутина раз в 100 мс вызывает `producer.poll(0)` для разгребания delivery queue). Это небольшой overhead, который съедает 6%.
4. **На 2-ядерной машине bottleneck — общий CPU воркеров**, не Kafka-слой. pydantic, FastAPI, uvicorn routing вместе кушают больше, чем producer.send(). Оптимизация только producer'а не помогает.

## Вывод

**Для нашего сценария оставляем aiokafka.** Он даёт +6% RPS и есть в коде проекта уже.

Confluent становится интересен в двух случаях:
- **SLA по p95/p99** — когда важнее предсказуемость хвоста, чем пропускная способность. Тогда 1.26s vs 1.61s — существенная разница.
- **CPU-разгруженная машина** — если ядер будет больше, confluent может начать выигрывать за счёт реальной параллельности send + handler. На 2 ядрах мы CPU-насыщены.

### Главный урок этого эксперимента

Прежде чем искать сложные архитектурные рычаги (сменить драйвер, сменить фреймворк), **всегда сначала отключить логи и убедиться что замер честный**. Мы тут кружили вокруг нескольких экспериментов, пока не обнаружили, что 15% CPU уходило на access-log — банальная конфигурационная вещь, которую покрывает одна CLI-опция.
