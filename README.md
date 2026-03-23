# FastAPI + Kafka + ClickHouse

Тестовый проект для нагрузочного тестирования (k6).

## Запуск

```bash
docker-compose up -d --build
```

## Проверка

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"test","email":"test@example.com"}'
```

## Сервисы

| Сервис     | Порт |
|------------|------|
| FastAPI    | 8000 |
| Kafka      | 9092 |
| ClickHouse | 8123 |
