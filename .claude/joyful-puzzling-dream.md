# План: Отчёт по масштабированию uvicorn workers

## Context

Команда протестировала систему (FastAPI → Kafka → Consumer → ClickHouse) на Docker/WSL2 с разным числом uvicorn workers: 1, 4, 8 — все три конфигурации **не прошли** threshold `p(95)<300ms` (~345ms). С 6 воркерами тест прошёл. Это контринтуитивно и требует объяснения для клиента и команды.

Тест: `k6 run --vus 100 --duration 1m k6/k6.js` — 100 VU бьют в `POST /users/batch/1` 1 минуту.

## Что делаем

Создаём файл `docs/WORKER_SCALING_ANALYSIS.md` — подробный теоретический отчёт на русском языке с двумя основными разделами:

### Раздел 1: Почему увеличение воркеров [1, 4, 8] не помогло

Теория, привязанная к нашей системе:

1. **Модель воркеров uvicorn** — каждый `--workers N` форкает N процессов. Каждый создаёт свой KafkaProducer singleton (`kafka_app/producer.py:7-22`). N воркеров = N TCP-соединений к одному брокеру.

2. **GIL — почему это НЕ причина** — воркеры это процессы (multiprocessing), не потоки. У каждого свой GIL.

3. **WSL2 ресурсы** — Docker на WSL2 делит CPU/RAM между API, Kafka JVM, Zookeeper JVM, ClickHouse, Consumer. Эффективных ядер для API мало.

4. **Context switching** — при W > доступных ядер, OS переключает процессы. Каждое переключение: 1-10 мкс + инвалидация кеша. При 8 воркерах + инфраструктура = деградация tail latency.

5. **Конкуренция за Kafka** — `producer.flush()` (`kafka_app/user_producer.py:16`) синхронный, блокирует до подтверждения. 100 VU × N воркеров = N параллельных flush() к одной партиции. Всё сериализуется на уровне partition leader.

6. **Закон Амдала** — Speedup = 1/(S + (1-S)/N). Если flush() занимает 60-70% времени запроса, даже бесконечные воркеры дают максимум 1.4-1.7x. С накладными расходами — ускорение может быть отрицательным.

7. **Закон Литтла** — L = λ × W. При 100 VU и ~219ms latency: λ = 456 req/s (совпадает с res2.md). Воркеры не меняют L и не уменьшают W (latency = Kafka I/O).

8. **Memory pressure** — каждый процесс ~50 MB + KafkaProducer buffer (32 MB). 8 воркеров = ~656 MB. Плюс Kafka JVM, ClickHouse, ZK — может превышать лимит WSL2.

9. **Почему 6, а не 4 и не 8** — гипотеза: машина ~4 физ. ядра / 8 логических. Workers=6 — оптимальный overlap между CPU (prepare_user) и I/O (flush). Workers=4 — недостаточно overlap. Workers=8 — context switching съедает выигрыш. Разница между прошёл/не прошёл = ~15% (300 vs 345ms) — в зоне влияния context switching.

### Раздел 2: Как определить оптимальное число воркеров

1. **Классические формулы**: CPU-bound = cores, I/O-bound = 2×cores+1, Mixed = cores × (1 + wait/compute)
2. **Определение характера нагрузки**: профилирование CPU vs I/O
3. **Методология поиска**: baseline с 1 → cores → 2×cores → бинарный поиск между лучшими
4. **Что измерять**: p95/p99, RPS, CPU/memory (docker stats), context switches
5. **Признаки избытка**: p95 растёт при стабильном p50, CPU 100% но throughput падает
6. **Признаки недостатка**: CPU < 100%, линейный рост от +1 воркера
7. **Учёт инфраструктуры**: effective_cores = total - infra_overhead
8. **Кривая убывающей отдачи**: график workers vs throughput/p95

### Рекомендации

- Текущие 6 воркеров — рабочий вариант, но специфичен для машины
- Рассмотреть `aiokafka` вместо `kafka-python` (async flush)
- Добавить Kafka partitions (сейчас 1) для снижения contention
- Провести повторное тестирование 1→8 с фиксацией метрик `docker stats`

## Файлы

| Действие | Файл |
|----------|------|
| **Создать** | `docs/WORKER_SCALING_ANALYSIS.md` |

## Ключевые файлы для ссылок в отчёте

- `kafka_app/producer.py` — singleton KafkaProducer, flush()
- `kafka_app/user_producer.py` — send_users_batch() с синхронным flush()
- `app/routers/users.py` — endpoint POST /users/batch/{n}
- `Dockerfile` — текущие `--workers 6`
- `k6/res2.md` — результат теста (456 RPS, p95=345ms)
- `docs/PIPELINE_BENCHMARK_240325_5.md` — предыдущий бенчмарк с 1 воркером

## Верификация

- Прочитать готовый файл и убедиться что теория корректна
- Проверить что все ссылки на код актуальны
