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
curl -X POST http://localhost:8000/users/batch/1000
```

Ответ:
```json
{"sent": 1000, "saved_to_clickhouse": 1000}
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
