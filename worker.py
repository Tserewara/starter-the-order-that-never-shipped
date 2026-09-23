import json
import os
import sqlite3
import time
from datetime import datetime, timezone

import pika

DB_PATH = os.environ.get("DB_PATH", "orders.db")
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")


def record(message):
    connection = sqlite3.connect(DB_PATH, timeout=3)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS fulfillment_attempts (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, order_id TEXT, created_at TEXT)"
    )
    connection.execute(
        "INSERT INTO fulfillment_attempts (event_id, order_id, created_at) VALUES (?, ?, ?)",
        (message["event_id"], message["order_id"], datetime.now(timezone.utc).isoformat()),
    )
    connection.commit()
    connection.close()


def main():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, connection_attempts=20, retry_delay=1))
            channel = connection.channel()
            channel.queue_declare(queue="orders", durable=True)
            channel.basic_qos(prefetch_count=1)

            def handle(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    record(message)
                    print(json.dumps({"event": "fulfilled", "event_id": message["event_id"], "order_id": message["order_id"]}), flush=True)
                    crash_path = os.path.join(os.path.dirname(DB_PATH) or ".", "crash-after-record")
                    if os.path.exists(crash_path):
                        os.remove(crash_path)
                        os._exit(23)
                    ch.basic_ack(method.delivery_tag)
                except Exception as exc:
                    print(json.dumps({"event": "message_rejected", "error": type(exc).__name__}), flush=True)
                    ch.basic_nack(method.delivery_tag, requeue=False)

            channel.basic_consume(queue="orders", on_message_callback=handle)
            channel.start_consuming()
        except Exception as exc:
            print(json.dumps({"event": "worker_connection_lost", "error": type(exc).__name__}), flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
