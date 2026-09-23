# Orders that need to reach the warehouse

A small order API and the warehouse worker that consumes its events. The API listens on `http://localhost:8000`, and RabbitMQ's management UI is at `http://localhost:15672` (`guest` / `guest`).

`make up` starts everything, `make test` runs the tests in a container, `make stats` prints the order and warehouse counters, and `make down` stops the stack.

`POST /orders` takes `customer` and `sku` fields and returns an order id and an event id. For rehearsals there are `POST /admin/replay/<event_id>`, `POST /admin/poison` and `GET /admin/stats`, and `make pause-broker` and `make resume-broker` stop and start the broker.

`make arm-crash` makes the worker exit on its next delivery, after it writes the warehouse record and before it acknowledges the message; `make start-worker` brings it back and `make stop-worker` kills it. `make deliveries` creates 1,000 orders, replays every event id once, waits for the warehouse count to settle, and prints `orders`, `unique_fulfilled_events`, `fulfillment_attempts` and `duplicate_side_effects`. `make stats` shows the same counters at any time.

The code is deliberately small, the kind of service you inherit. The database is a SQLite file in a named volume, so the API and the worker share the same durable state.
