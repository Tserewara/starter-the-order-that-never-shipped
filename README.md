# BrasaCart checkout

Checkout takes orders, and the warehouse picks them. Every paid order has to
turn into a row in the warehouse's picking feed, and the warehouse packs one
box for every row it finds there.

```
service/    checkout: the API and the warehouse worker, Python and Flask
harness/    RabbitMQ, the warehouse feed (Postgres), and the tools the drills use
contract/   black-box tests of what checkout answers
```

## Run

You need Docker with Compose, nothing else. `make up` starts the API
(`http://localhost:8000`), the worker, RabbitMQ and the warehouse feed.
`make contract` runs the contract tests; `make down` removes everything,
volumes included.

`POST /orders` takes `{"customer": "...", "sku": "..."}` and answers with
the `order_id` and the `event_id` of the event it sends to the warehouse:
201 when the event went out, 202 when it didn't. `POST
/admin/replay/{event_id}` sends an order's event again, the way operators
replayed events after Tuesday's outage.

## Break it

- `make outage` pauses the broker, sends 100 orders, brings the broker back,
  waits for the feed to settle and prints:

  ```
  accepted=100 in_warehouse=N lost=N duplicates=N
  ```

  counted in the warehouse feed for those 100 orders: `lost` is an accepted
  order with no pick, `duplicates` the picks beyond one per order.
- `make deliveries` sends 1,000 orders, waits, replays every one of their
  events, waits again and prints the same counts for the 1,000
  (`orders=1000 in_warehouse=N lost=N duplicates=N`). It takes a minute or
  two. Restart the worker while it runs with `make stop-worker` (a hard kill)
  and `make start-worker`.
- `make pause-broker` and `make resume-broker` do the pause by hand.
- `make picks` prints `picks=N orders=N duplicates=N` for the whole feed.
- RabbitMQ's management page is at `http://localhost:15672` (guest/guest).

## Porting the service

Checkout is Python and Flask; you can write it in another language. It is one
image, built from `service/Dockerfile`, that runs as `api` (port 8000) and as
`worker`, both sharing `/state` and reading `DB_PATH`, `RABBITMQ_HOST` and
`WAREHOUSE_URL`. The worker writes picks to the warehouse's `picks` table
(`event_id`, `order_id`). Anything else that has to run in the background
goes in the `worker` role. Run `make contract` until it passes.

## License

MIT. See `LICENSE`.
