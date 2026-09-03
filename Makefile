PROJECT=bgym_order
.PHONY: up down test pause-broker resume-broker stats

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
