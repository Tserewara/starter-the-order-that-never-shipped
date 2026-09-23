import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone

import pika
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "orders.db")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")


def db():
    connection = sqlite3.connect(DB_PATH, timeout=3)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, event_id TEXT UNIQUE, customer TEXT, sku TEXT, created_at TEXT)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS fulfillment_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, order_id TEXT, created_at TEXT)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS publish_failures (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, created_at TEXT)"
    )
    connection.commit()
    return connection


def publish(message):
    connection = pika.BlockingConnection(
        # A paused broker accepts the TCP connection and then never answers;
        # without a bound, each order would wait out pika's 15s handshake.
        pika.ConnectionParameters(
            host=RABBITMQ_HOST, connection_attempts=1, socket_timeout=1, stack_timeout=2
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue="orders", durable=True)
    channel.basic_publish(
        exchange="", routing_key="orders", body=json.dumps(message).encode(),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    order_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    connection = db()
    connection.execute(
        "INSERT INTO orders (id, event_id, customer, sku, created_at) VALUES (?, ?, ?, ?, ?)",
        (order_id, event_id, data.get("customer", "guest"), data.get("sku", "unknown"), now),
    )
    connection.commit()
    message = {"event_id": event_id, "order_id": order_id, "customer": data.get("customer", "guest"), "sku": data.get("sku", "unknown")}
    published = True
    try:
        publish(message)
    except Exception as exc:
        published = False
        connection.execute("INSERT INTO publish_failures (order_id, created_at) VALUES (?, ?)", (order_id, now))
        connection.commit()
        print(json.dumps({"event": "publish_failed", "order_id": order_id, "error": type(exc).__name__}), flush=True)
    connection.close()
    return jsonify({"order_id": order_id, "event_id": event_id, "published": published}), 201 if published else 202


@app.post("/admin/replay/<event_id>")
def replay(event_id):
    connection = db()
    row = connection.execute("SELECT * FROM orders WHERE event_id = ?", (event_id,)).fetchone()
    connection.close()
    if not row:
        return {"error": "unknown event"}, 404
    publish({"event_id": row["event_id"], "order_id": row["id"], "customer": row["customer"], "sku": row["sku"]})
    return {"replayed": event_id}


@app.post("/admin/poison")
def poison():
    publish({"event_id": str(uuid.uuid4()), "order_id": "malformed"})
    return {"published": True}, 202


@app.get("/admin/stats")
def stats():
    connection = db()
    result = {
        "orders": connection.execute("SELECT count(*) FROM orders").fetchone()[0],
        "fulfillment_attempts": connection.execute("SELECT count(*) FROM fulfillment_attempts").fetchone()[0],
        "publish_failures": connection.execute("SELECT count(*) FROM publish_failures").fetchone()[0],
    }
    connection.close()
    return result


if __name__ == "__main__":
    db().close()
    app.run(host="0.0.0.0", port=8000)
