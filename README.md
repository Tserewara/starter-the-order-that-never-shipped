# Orders that need to reach the warehouse

This is a small order API and warehouse worker. The API is available at
`http://localhost:8000`; RabbitMQ has its management UI at
`http://localhost:15672` with `guest` / `guest`.

Run `make up` to start the services and `make test` to run the tests in a
container. `make stats` shows the order and warehouse counters. Stop the stack
with `make down`.

The API accepts `POST /orders` with `customer` and `sku` fields. The response
contains an order id and an event id. The local control endpoints are
`POST /admin/replay/<event_id>`, `POST /admin/poison`, and `GET /admin/stats`.
`make pause-broker` and `make resume-broker` control the local broker for a
failure rehearsal.

The repository is intentionally a small inherited service. Its database is a
SQLite file in a named volume so the API and worker share the same durable
state.
