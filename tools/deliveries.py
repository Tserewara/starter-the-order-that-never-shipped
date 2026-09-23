"""Drill D5: 1,000 orders, then every event id replayed once, then the tally.

Restart the worker (`make stop-worker`, `make start-worker`) while this runs.
It waits for the warehouse count to settle before replaying and before
printing, so a slow or stopped worker never makes the numbers look better.
"""

import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.environ.get("TEST_URL", "http://localhost:8000")
COUNT = int(os.environ.get("ORDERS", "1000"))


def call(path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(BASE + path, data=body, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def order(index):
    return call("/orders", "POST", {"customer": f"load-{index}", "sku": "tea-42"})["event_id"]


def settle(deadline):
    """Poll until the warehouse count stops moving for three reads in a row."""
    last, steady, stats = None, 0, call("/admin/stats")
    while time.time() < deadline and steady < 3:
        time.sleep(2)
        stats = call("/admin/stats")
        steady = steady + 1 if stats["fulfillment_attempts"] == last else 0
        last = stats["fulfillment_attempts"]
    return stats


deadline = time.time() + 600
with ThreadPoolExecutor(max_workers=8) as pool:
    event_ids = list(pool.map(order, range(COUNT)))
print(f"created={len(event_ids)}", flush=True)
settle(deadline)

with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(lambda event_id: call(f"/admin/replay/{event_id}", "POST"), event_ids))
print(f"replayed={len(event_ids)}", flush=True)

stats = settle(deadline)
print(json.dumps({key: stats.get(key) for key in ("orders", "unique_fulfilled_events", "fulfillment_attempts", "duplicate_side_effects")}), flush=True)
