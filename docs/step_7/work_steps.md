
# 1. Обновить config.py
KAFKA_ENGINE_NUM_CONSUMERS = 8

# 2. Обновить kafka_app/producer.py
# linger_ms=100, max_batch_size=131072

# 3. Обновить docker-compose.yml
UVICORN_WORKERS: 4
KAFKA_NUM_PARTITIONS: 8

# 4. Пересоздать
make full-clean && make up

# 5. Изменить партиции
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --alter --topic users --partitions 8

# 6. Тестировать
k6 run --vus 2500 --duration 1m k6/rps.js


> Python для отключения idempotent writes

Ключевые изменения
✅ idempotent=False в producer — главная оптимизация (Go отключает это, Python включал по умолчанию)
✅ linger_ms=100 (было 20) — лучше батчинг
✅ max_batch_size=128KB (было 64KB) — крупнее батчи
✅ KAFKA_NUM_PARTITIONS=8 (было 4) — больше параллелизма
✅ KAFKA_ENGINE_NUM_CONSUMERS=8 (было 4) — ClickHouse читает быстрее
✅ UVICORN_WORKERS=4 (было 5) — оптимально для 4 логических потоков


### Запуск теста

```
# Полная очистка и запуск
make full-clean && make up

# Увеличить партиции
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --alter --topic users --partitions 8

# Нагрузка
k6 run --vus 2500 --duration 1m k6/rps.js
```
_Прогноз: RPS ~4.5-5.5k, p95 ~1.0-1.2s_