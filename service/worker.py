"""The warehouse worker: every order event becomes a row in the picking feed."""

import json
import os
import time

import pika
import psycopg

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
WAREHOUSE_URL = os.environ["WAREHOUSE_URL"]


def pick(message):
    with psycopg.connect(WAREHOUSE_URL) as conn:
        conn.execute("INSERT INTO picks (event_id, order_id) VALUES (%s, %s)", (message["event_id"], message["order_id"]))


def main():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, connection_attempts=20, retry_delay=1))
            channel = connection.channel()
            channel.queue_declare(queue="orders", durable=True)
            channel.basic_qos(prefetch_count=1)

            def handle(ch, method, properties, body):
                message = json.loads(body)
                pick(message)
                print(json.dumps({"event": "picked", "event_id": message["event_id"], "order_id": message["order_id"]}), flush=True)
                ch.basic_ack(method.delivery_tag)

            channel.basic_consume(queue="orders", on_message_callback=handle)
            channel.start_consuming()
        except Exception as exc:
            print(json.dumps({"event": "worker_connection_lost", "error": type(exc).__name__}), flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
