PROJECT=bgym_order
.PHONY: up down test pause-broker resume-broker stats arm-crash stop-worker start-worker deliveries

up:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose up -d --build

down:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose down -v

test:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose run --rm test

pause-broker:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose pause rabbitmq

resume-broker:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose unpause rabbitmq

stats:
	curl -fsS http://localhost:8000/admin/stats

arm-crash:
	curl -fsS -X POST http://localhost:8000/admin/arm-crash

stop-worker:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose kill worker

start-worker:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose start worker

deliveries:
	COMPOSE_PROJECT_NAME=$(PROJECT) docker compose run --rm --build -e TEST_URL=http://api:8000 test python3 tools/deliveries.py
