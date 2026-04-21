# Тюнинг aiokafka producer

**Дата:** 21.04.2026 | **Среда:** Docker/WSL2, i3-1005G1 (2c/4t) | **Инструмент:** k6
**Базовая конфигурация:** FastAPI + aiokafka, uvicorn --workers 4, Kafka 2 partitions

## Что сделали

Три изменения в producer:

**`kafka_app/producer.py`** — добавили тюнинг параметров:
```python
AIOKafkaProducer(
    ...
    linger_ms=20,            # накапливать батч до 20мс между запросами
    max_batch_size=65536,    # 64 KB (было 16 KB)
    compression_type="lz4",  # сжатие (было без)
    acks=1,
)
```

**`kafka_app/user_producer.py`** — убрали `await producer.flush()` per-request. HTTP возвращает ответ сразу после enqueue в буфер aiokafka.

**`requirements.txt`** — `aiokafka` → `aiokafka[lz4]`.

## Результаты (VU vs RPS, tuned)

| VU | RPS | median | p95 | max | Errors | Зона |
|---|---|---|---|---|---|---|
| 1200 | 2151 | 430ms | **936ms** | 37.8s | 0% | пик |
| 1400 | 1978 | 456ms | 1.91s | 30.9s | 0% | плато (шум) |
| 1600 | 2174 | 629ms | 1.72s | 11s | 0% | плато |
| 1800 | 2161 | 676ms | 1.73s | 24.1s | 0% | плато |
| 2000 r1 | 1485 | 734ms | 2.22s | 58.8s | 0.39% | выброс WSL2 |
| 2000 r2 | 2127 | 635ms | 2.11s | 39.8s | 0% | плато |
| 2500 r1 | 2057 | 518ms | 1.3s | 58.6s | 0.25% | soft cliff (bimodal) |
| 2500 r2 | 1823 | 1.11s | 2.77s | 33.1s | 0% | soft cliff (slow all) |

## Сравнение с baseline (async+2p без тюнинга)

| Метрика | Baseline | Tuned | Δ |
|---|---|---|---|
| Пик RPS | 1783 | **~2150** | **+21%** |
| p95 на пике | ~1.8s | **936ms** | −48% |
| Ширина плато | ~400 VU | **~800 VU** | ×2 |
| Cliff | VU≈1400 (жёсткий, 60% err) | VU≈2500 (мягкий, 0.25% err) | +1100 VU |

## Вывод

**Что помогло больше всего:**

1. **Убранный `flush()` per-request** — главный вклад. HTTP не ждёт ack от Kafka, median упал с ~1.2s до ~430ms.
2. **`linger_ms=20`** — накопление батча между параллельными запросами снизило количество RPC к брокеру.
3. **`compression_type="lz4"`** — меньше I/O, CPU-cheap. Синергично с большими батчами.
4. **`max_batch_size=65536`** — крупнее батчи = меньше оверхеда на сообщение.

На пике дали **+21% RPS**, плато расширилось вдвое, cliff сместился с жёсткого (VU=1400, 60% ошибок) на мягкий (VU=2500, 0.25% ошибок с bimodal деградацией).

---

## Финальный стейт (layered optimizations)

Поверх producer-тюнинга добавили ещё три изменения, каждое замеряли отдельно:

| Слой | Что | Вклад на VU=2500 |
|---|---|---|
| **orjson** | `value_serializer`: `json.dumps` → `orjson.dumps` | +14% RPS (1986→2183) |
| **no-log** | Убран `logger.info` per-request в `send_users_batch` | Освободил CPU, лучше консистентность |
| **workers=5** | uvicorn workers: 4 → 5 (env-driven через `UVICORN_WORKERS`) | +1.6% RPS, нет зависших VU |
| **broker threads** | `KAFKA_NUM_NETWORK_THREADS=6`, `KAFKA_NUM_IO_THREADS=16` | 0% ошибок (было 0.09%) |

### Финальная конфигурация

```python
# kafka_app/producer.py
AIOKafkaProducer(
    ...
    value_serializer=lambda v: orjson.dumps(v),
    linger_ms=20,
    max_batch_size=65536,
    compression_type="lz4",
    acks=1,
)
```

```yaml
# docker-compose.yml (kafka service)
KAFKA_NUM_PARTITIONS: 2
KAFKA_NUM_NETWORK_THREADS: 6
KAFKA_NUM_IO_THREADS: 16
```

```dockerfile
# Dockerfile
CMD uvicorn app.main:app --workers 5
```

### Финальный результат

| Метрика | Значение |
|---|---|
| **Пик RPS** | **2177 @ VU=2500** |
| **p95** | **2.18s** @ VU=2500 |
| **Errors** | **0%** |
| **Плато** | VU=1200–2500 |
| **Cliff** | ~VU=2800–3000 (soft, bimodal) |
| **Лучший p95** | **1.11s @ VU=1600** (RPS 2174) |

### Эволюция (полная)

| Стадия | Пик RPS | p95 на пике |
|---|---|---|
| Sync + 1p (baseline) | 760 | ~1.6s |
| Async + 2p | 1780 | ~1.8s |
| + producer tune | 2150 | 936ms |
| + orjson | 2140 | 989ms (VU=2500: +14%) |
| + no log | 2140 | 989ms (консистентнее) |
| + 5 workers | 2183 | 1.9s |
| **+ broker threads** | **2177** | **2.18s (0% errors)** |

**Суммарный прирост: ×2.87 от baseline (760 → 2177 RPS).**

## Что проверили и отклонили

| Изменение | Результат |
|---|---|
| `linger_ms=50, max_batch_size=128KB` | −8% RPS (buffer pressure) |
| `acks=0` (fire-and-forget) | −14% RPS (неожиданно) |
| `compression_type=None` | −6% RPS (lz4 полезен даже на Docker loopback) |
| Pydantic skip (dicts вместо моделей) | −8% RPS (pydantic-core на Rust быстрее ручного Python) |
| 3 Kafka partitions | −2% RPS, но 14× меньше ошибок (альтернатива для reliability) |
| 4 Kafka partitions | −2% RPS, **3.5× больше ошибок** (context switching на 2 ядрах) |

**Вывод:** текущая комбинация — локальный оптимум для 2-ядерного железа. Дальнейшее улучшение требует архитектурной смены (ClickHouse Kafka Engine — отдельный step_4) или перехода на более мощное железо.
