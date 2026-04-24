# Step 6 — Оптимизация Python-пайплайна

Цель шага: докопать оставшийся разрыв с Go-прототипом (x3.47) со стороны Python. Идём от самых дешёвых проверок к более тяжёлым.

---

## Эксперимент 1: Fire-and-forget Kafka producer (без await)

### Гипотеза

`await producer.send(...)` в цикле — handler блокируется, пока aiokafka не положит каждое сообщение в свою accumulator-очередь. Для batch из 1 сообщения это одна `send()`, но при 2000+ RPS на воркер — десятки тысяч awaitов в секунду, каждый переключает event loop.

Если убрать await и пустить send через `asyncio.create_task` — handler возвращает 200 **сразу** после создания задачи, а отправка происходит в фоне на том же event loop. Ожидание: +5–10% RPS.

### Что меняем

Файл: [kafka_app/user_producer.py](../../kafka_app/user_producer.py)

**Было:**
```python
async def send_users_batch(producer, users) -> int:
    for user in users:
        await producer.send(
            KAFKA_TOPIC_USERS, key=user.id, value=user.model_dump()
        )
    return len(users)
```

**Стало:**
```python
import asyncio

async def send_users_batch(producer, users) -> int:
    for user in users:
        asyncio.create_task(
            producer.send(
                KAFKA_TOPIC_USERS, key=user.id, value=user.model_dump()
            )
        )
    return len(users)
```

**Почему нельзя просто убрать `await`:** `producer.send(...)` — корутина, не Future. Без `await` или `create_task` Python кинет `RuntimeWarning: coroutine was never awaited`, и сообщение никогда не попадёт в брокер. `asyncio.create_task` шедулит корутину на event loop, возвращая Task сразу.

### Компромисс (tradeoff)

- **Handler возвращает 200 до того, как сообщение попало даже в aiokafka-очередь.** Если брокер недоступен / буфер переполнен / воркер падает — сообщение тихо теряется.
- **Ошибки send() теряются** — Task никто не await'ит, exception поглощается (aiokafka залогирует, но в response 200 уже ушёл).
- **Порядок по ключу сохраняется** — aiokafka внутри сериализует по partition'у.

Для users-данных durability-критична, в проде так делать не стоит. Тут — локальный бенч, риск допустимый.

### Как замеряем

Baseline (из backlog): **2247 RPS @ VU=2500**, p95=1.52s, errors=0.43%. 

```bash
# Пересобрать api с новым кодом
docker compose up -d --build --force-recreate api

# Подождать пока поднимется, затем:
cd /home/apik6 && VUS=2500 DURATION=1m k6 run k6/rps.js
```

Прогоняем 2–3 раза подряд, берём медианный результат.

### Результат (первый заход — 3 прогона fire-and-forget)

| # | RPS | p(95) | p(95) ok-only | errors | VUs min |
|---|---|---|---|---|---|
| 1 | **2155** | 1.05s | 1.03s | 0.56% | 20 (артефакт?) |
| 2 | 1660 | 3.00s | 2.93s | 0.13% | 393 |
| 3 | 1843 | 2.16s | 2.15s | 0.15% | 216 |
| **медиана** | **1843** | 2.16s | 2.15s | 0.15% | |

Baseline из `optimization_backlog.md` (измерен 2026-04-23): **2247 RPS**, p95=1.52s, errors=0.43%.

### Наблюдения

1. **Медиана F&F ниже baseline на 18%**, p95 хуже почти в 1.5 раза. На первый взгляд — регрессия, а не win.
2. **Дисперсия 30% между прогонами** (1660 ↔ 2155). На таком разбросе один прогон ничего не доказывает.
3. **Прогон #1 выбивается вверх** (2155 RPS, p95=1.05s — лучше baseline). У него же странный `VUs min=20`. Похоже на артефакт тёплого старта.
4. **Errors стабильно ниже baseline** (0.13–0.56% против 0.43%). Вероятно, побочный эффект fire-and-forget: handler возвращает 200 до broker ack, меньше шансов попасть в k6 timeout (значит, меньше «failed» статусов).
5. Baseline 2247 зафиксирован ~ неделю назад. С тех пор могли быть дрейфы (WSL, Docker-кэши, background-процессы). Без контрольного прогона сравнение нечестное.

### Предварительный вывод

**Не win при текущем измерении**, но **результат нельзя считать финальным** — нужен контрольный A/B в одной сессии:

1. Откатить `user_producer.py` на `await`
2. 3 прогона — today's baseline
3. Снова применить F&F, 3 прогона
4. Сравнить медианы — только так поймём, это F&F просел или baseline в backlog устарел

### Follow-up: контрольный A/B

<!-- заполнить после контрольных прогонов -->

### Итоговый вывод

<!-- после A/B: взять / откатить / идти дальше в P1 -->
