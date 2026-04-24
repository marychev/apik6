# Эксперимент 4: cross-request coalescing через asyncio.Queue

## Гипотеза

`aiokafka` батчит на сетевом слое (`linger_ms=20 + batch_size=64KB`), но внутри каждого handler'а:
- `await producer.send()` делает Python-работу: сериализация, партиционирование, append в accumulator
- каждая concurrent-корутина дёргает это независимо

Если собрать сообщения из concurrent-handler'ов в один asyncio.Queue и фоновым task'ом дрейнить пачками через `asyncio.gather(*sends)` — ожидали:
- handler'ы возвращаются быстрее (не ждут Python-работу aiokafka)
- одна пачка из N сообщений идёт с меньшим per-message overhead
- backpressure через `Queue(maxsize=...)` — в отличие от F&F `create_task`, ошибки не теряются

Ожидание: **+5–15% RPS**, ноль потерь.

## Архитектура

Новое приложение [app_batched/](../../app_batched/) на порту 8004, профиль `batched`.

```
POST /users/batch/1
    │
    ▼
handler: await queue.put(user)  ─────►  asyncio.Queue (maxsize=10_000)
    │                                            │
    ▼                                            ▼
return {"sent": 1}                       _batcher() task (в lifespan):
                                            while True:
                                              first = await queue.get()
                                              drain queue_nowait → batch (≤ 100)
                                              await asyncio.gather(
                                                *[producer.send(TOPIC, key, value)
                                                  for u in batch],
                                                return_exceptions=True)
                                              log failed if any
```

Код: [app_batched/main.py](../../app_batched/main.py)

Идентично baseline: FastAPI, pydantic v2, orjson, aiokafka с теми же настройками (`linger_ms=20, batch_size=64KB, lz4, acks=1`), uvicorn `--no-access-log`, workers=5.

## Результаты

| # | RPS | p(95) | errors | max duration |
|---|---|---|---|---|
| 1 | 2759 | 2.53s | 0% | 29.69s |
| 2 | 3093 | 2.13s | 0% | 10.67s |
| 3 | 3144 | 2.11s | 0% | 30.31s |
| **медиана** | **3093** | **2.13s** | **0%** | |

Логи `api_batched`: 17 строк, никаких exception/error/fail. Batcher не потерял ни одного сообщения.

### Сравнение со всеми конфигурациями

| Стек | Медиана RPS | p(95) | errors | Delivery |
|---|---|---|---|---|
| aiokafka + await + no-access-log (baseline) | 3322 | 1.61s | 0% | ✅ |
| confluent + no-access-log | 3127 | **1.26s** | 0% | ✅ |
| **aiokafka + queue+batcher** | **3093** | 2.13s | 0% | ✅ |

**Batched проиграл baseline на 7% RPS и на 32% по p(95).**

## Почему batcher оказался хуже

1. **aiokafka уже батчит внутри.** `linger_ms=20 + batch_size=64KB` группирует concurrent send'ы автоматически. Application-level batcher делает двойную работу.
2. **Single batcher task = bottleneck.** В baseline каждый handler независимо добавляет в aiokafka.accumulator (thread-safe, lock-free). В batched всё проходит через **одну** фоновую корутину — это точка серилизации, а не параллелизма.
3. **Extra hop = extra latency.** Два лишних context-switch'а (handler→queue, queue→batcher) добавляют ~100–500 μs per-message, прямо отражаются в p(95) +32%.
4. **`asyncio.gather(*sends)` не помогает.** aiokafka всё равно собирает в один linger-бакет; вызов N `send()` одновременно не даёт нового выигрыша.

## Вывод

**Не принимаем.** Паттерн с application-level очередью дублирует механизм aiokafka и добавляет overhead. Baseline (`await producer.send()` напрямую) остаётся победителем.

Это ценный **negative result**: «собирать пачкой перед отправкой» — плохая интуиция, когда underlying библиотека уже делает это. Имело бы смысл только:
- при тяжёлом кастомном сериализаторе (у нас orjson = C + pydantic v2 = Rust — некуда оптимизировать)
- при реальном `producer.send_batch()` с ручной маршрутизацией по партициям (минуя accumulator) — но это 50+ строк кода на 10% выигрыш в лучшем случае

Прототип `app_batched/` оставляем в репо как reference — если когда-нибудь появится тяжёлый pre-send хук, шаблон готов.

## Общий рейтинг step_6

| Место | Конфигурация | RPS | p(95) | Лучше для |
|---|---|---|---|---|
| 🥇 | aiokafka + await + no-access-log | **3322** | 1.61s | throughput |
| 🥈 | confluent + await + no-access-log | 3127 | **1.26s** | latency |
| 🥉 | aiokafka + queue+batcher + no-access-log | 3093 | 2.13s | — (не нужен) |
| | Old baseline (with access-log) | 2247 | 1.52s | — (deprecated) |

**Главный рычаг step_6:** `uvicorn --no-access-log` (+48% от old baseline). Всё остальное — шум в пределах ±6%.
