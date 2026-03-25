.PHONY: up down build logs restart ps clean k6-throughput k6-spike k6-consumer-lag

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

restart:
	docker compose down && docker compose up -d --build

ps:
	docker compose ps

clean:
	docker compose down -v --remove-orphans

k6-throughput:
	k6 run k6/throughput.js

k6-spike:
	k6 run k6/spike.js

k6-consumer-lag:
	k6 run k6/consumer_lag.js
