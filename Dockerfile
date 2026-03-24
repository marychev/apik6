FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py .
COPY app/ app/
COPY kafka_app/ kafka_app/
COPY clickhouse_app/ clickhouse_app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
