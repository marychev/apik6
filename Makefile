.PHONY: up down build logs restart ps k6-throughput k6-spike k6-soak k6-breakpoint k6-integrity

up:
	docker-compose up -d --build

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

restart:
	docker-compose down && docker-compose up -d --build

ps:
	docker-compose ps

k6-throughput:
	k6 run k6/throughput.js

k6-spike:
	k6 run k6/spike.js

k6-soak:
	k6 run k6/soak.js

k6-breakpoint:
	k6 run k6/breakpoint.js

k6-integrity:
	k6 run k6/data-integrity.js
