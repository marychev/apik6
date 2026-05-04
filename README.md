# FastAPI + Kafka + ClickHouse

Пайплайн: API создает пользователей, отправляет в Kafka, consumer пишет в ClickHouse.

```
POST /users → [API] → Kafka (topic: users) → [Consumer] → ClickHouse (table: users)
```

## Структура проекта

```
app/                    # FastAPI приложение
├── main.py             # точка входа, lifespan
├── routers/users.py    # эндпоинты
├── schemas.py          # Pydantic-модели
└── services.py         # бизнес-логика

kafka_app/              # Kafka producer/consumer
├── producer.py         # get_producer() — singleton
├── consumer.py         # get_consumer()
├── user_producer.py    # отправка пользователей в Kafka
└── user_consumer.py    # чтение из Kafka → запись в ClickHouse

clickhouse_app/         # ClickHouse
├── client.py           # get_clickhouse_client() — singleton
└── init_db.py          # создание таблиц

config.py               # все константы (хосты, топики, таблицы)
```

## Запуск

```bash
make up        # поднять все сервисы
make logs      # логи
make down      # остановить
make restart   # пересборка и перезапуск
make ps        # статус контейнеров
```

## API

### Создать пользователя (+ отправка в Kafka)

```bash
curl -X POST http://localhost:8000/users/batch/1
```

### Сброс данных

```bash
curl -X POST http://localhost:8000/users/reset
```

## Проверка данных в ClickHouse

```bash
# Все записи
docker compose exec clickhouse clickhouse-client -q "SELECT * FROM users LIMIT 10"

# Количество
docker compose exec clickhouse clickhouse-client -q "SELECT count() FROM users"
```

## Проверка Kafka

```bash
# Список топиков
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Чтение сообщений
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic users --from-beginning
```

## Сервисы

| Сервис     | Порт |
|------------|------|
| FastAPI    | 8000 |
| Kafka      | 9092 (Docker), 9093 (localhost) |
| ClickHouse | 8123 (HTTP), 9000 (native) |
| Zookeeper  | 2181 |

## Конфигурация

Все константы в `config.py`. Хосты Kafka и ClickHouse можно переопределить через переменные окружения:

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9093
CLICKHOUSE_HOST=localhost
```

## Важные команды для тестирования и настройки

### Проверка Kafka топика

```bash
# Описание топика (партиции, репликация)
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic users

# Изменение количества партиций (если нужно увеличить)
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --alter --topic users --partitions 8
```

### Проверка ClickHouse таблицы

```bash
# Показать CREATE TABLE для users_kafka
docker compose exec clickhouse clickhouse-client --query="SHOW CREATE TABLE users_kafka"

# Изменение настроек Kafka Engine (если таблица уже существует)
docker compose exec clickhouse clickhouse-client --query="ALTER TABLE users_kafka MODIFY SETTING kafka_num_consumers=4, kafka_poll_timeout_ms=1000, kafka_poll_max_batch_size=200000, kafka_flush_interval_ms=10000"
```

### Пересоздание ClickHouse таблиц

```bash
# Удалить старые таблицы
docker compose exec clickhouse clickhouse-client --query="DROP TABLE IF EXISTS users_mv; DROP TABLE IF EXISTS users_kafka"

# Перезапустить API (init_db.py создаст таблицы заново)
docker compose restart api
```

### Нагрузочное тестирование

```bash
# Запуск k6 с 2500 VU на 1 минуту
k6 run --vus 2500 --duration 1m k6/k6.js

# Проверка количества записей после теста
docker compose exec clickhouse clickhouse-client --query="SELECT count() FROM users"
```

### Мониторинг

```bash
# Логи API
docker compose logs -f api

# Логи Kafka
docker compose logs -f kafka

# Логи ClickHouse
docker compose logs -f clickhouse
```
