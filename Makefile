COMPOSE = docker compose -f harness/compose.yaml
.PHONY: up down contract outage deliveries pause-broker resume-broker stop-worker start-worker picks logs

# The API, the worker, RabbitMQ and the warehouse feed.
up:
	$(COMPOSE) up -d --build --wait api worker

down:
	$(COMPOSE) down -v

# What the service already does, black-box. Passes before and after your change.
contract:
	$(COMPOSE) run --rm --build contract

# Tuesday: the broker pauses, 100 orders come in, the broker comes back.
outage:
	$(COMPOSE) build tools
	$(COMPOSE) pause rabbitmq
	$(COMPOSE) run --rm tools python3 outage.py create; $(COMPOSE) unpause rabbitmq
	$(COMPOSE) run --rm tools python3 outage.py check

# 1,000 orders, a replay of every event, then the tally. Restart the worker while it runs.
deliveries:
	$(COMPOSE) run --rm --build tools python3 deliveries.py

pause-broker:
	$(COMPOSE) pause rabbitmq
resume-broker:
	$(COMPOSE) unpause rabbitmq

stop-worker:
	$(COMPOSE) kill worker
start-worker:
	$(COMPOSE) start worker

# Rows in the warehouse feed, and how many orders have more than one.
picks:
	@$(COMPOSE) exec -T warehouse psql -U warehouse -tAc "SELECT 'picks=' || count(*) || ' orders=' || count(DISTINCT order_id) || ' duplicates=' || (count(*) - count(DISTINCT order_id)) FROM picks"

logs:
	$(COMPOSE) logs -f api worker
