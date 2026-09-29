import json
import os
import time
import urllib.error
import urllib.request

import psycopg

SERVICE = os.environ.get("SERVICE_URL", "http://api:8000")
WAREHOUSE_URL = os.environ.get("WAREHOUSE_URL", "postgresql://warehouse:warehouse@warehouse:5432/warehouse")


def call(path, method="GET", payload=None, timeout=30):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(SERVICE + path, data=body, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, json.loads(response.read())


def create_order(index, prefix):
    """POST /orders; returns (order_id, event_id), or None if the service refused it."""
    try:
        status, body = call("/orders", "POST", {"customer": f"{prefix}-{index}", "sku": "tea-42"})
    except (urllib.error.URLError, TimeoutError):
        return None
    return (body["order_id"], body["event_id"]) if status in (201, 202) else None


def picks():
    """(rows, rows per order_id) in the warehouse feed."""
    with psycopg.connect(WAREHOUSE_URL) as conn:
        rows = conn.execute("SELECT order_id, count(*) FROM picks GROUP BY order_id").fetchall()
    per_order = dict(rows)
    return sum(per_order.values()), per_order


def settle(deadline, expected=None):
    """Wait until the feed stops growing for three reads in a row, or every
    expected order is there."""
    last, steady = None, 0
    while time.time() < deadline and steady < 3:
        total, per_order = picks()
        if expected is not None and all(o in per_order for o in expected) and total == last:
            break
        steady = steady + 1 if total == last else 0
        last = total
        time.sleep(2)
    return picks()


def report(orders, per_order_before=None):
    """Counts for the orders this run created."""
    _, per_order = picks()
    before = per_order_before or {}
    delivered = [o for o in orders if per_order.get(o, 0) - before.get(o, 0) > 0]
    extra = sum(max(0, per_order.get(o, 0) - before.get(o, 0) - 1) for o in orders)
    return len(delivered), len(orders) - len(delivered), extra
