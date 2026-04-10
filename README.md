# Payment Processing Service

Асинхронный микросервис для обработки платежей с гарантированной доставкой событий.

## Возможности

- Создание и получение платежей через REST API
- Асинхронная обработка через RabbitMQ (FastStream)
- Outbox pattern для гарантированной публикации событий
- Dead Letter Queue для необработанных сообщений
- Webhook уведомления с retry (экспоненциальная задержка)
- Idempotency key для защиты от дублей
- Аутентификация через X-API-Key

## Стек

FastAPI, Pydantic v2, SQLAlchemy 2 (async), PostgreSQL, RabbitMQ, Alembic, Docker

## Запуск

### Docker

```bash
docker compose up --build
```

### Локально

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
uv run python -m src.consumer  # отдельный терминал
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `POSTGRES_USER` | Пользователь БД | `app` |
| `POSTGRES_PASSWORD` | Пароль БД | `app` |
| `POSTGRES_HOST` | Хост БД | `localhost` |
| `POSTGRES_PORT` | Порт БД | `5432` |
| `POSTGRES_DB` | Имя БД | `app` |
| `RABBITMQ_USER` | Пользователь RabbitMQ | `guest` |
| `RABBITMQ_PASSWORD` | Пароль RabbitMQ | `guest` |
| `RABBITMQ_HOST` | Хост RabbitMQ | `localhost` |
| `RABBITMQ_PORT` | Порт RabbitMQ | `5672` |
| `API_KEY` | Статический API ключ | `changeme` |
| `WEBHOOK_TIMEOUT` | Таймаут webhook запроса (сек) | `10.0` |
| `WEBHOOK_MAX_RETRIES` | Макс. попыток webhook | `3` |
| `WEBHOOK_BASE_DELAY` | Базовая задержка retry (сек) | `1.0` |

## Примеры

### Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "amount": "150.00",
    "currency": "RUB",
    "description": "Оплата заказа",
    "metadata": "{\"order_id\": 42}",
    "webhook_url": "https://example.com/webhooks/payment"
  }'
```

### Получение платежа

```bash
curl http://localhost:8000/api/v1/payments/{payment_id} \
  -H "X-API-Key: changeme"
```
