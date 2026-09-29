"""1,000 orders, then a replay of every one of their events, then the tally.

Restart the worker (`make stop-worker`, `make start-worker`) while this
runs. It waits for the warehouse feed to settle before replaying and before
printing, so a slow or stopped worker never makes the numbers look better.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor

from common import call, create_order, report, settle

COUNT = int(os.environ.get("ORDERS", "1000"))
deadline = time.time() + 600

with ThreadPoolExecutor(max_workers=8) as pool:
    results = [r for r in pool.map(lambda i: create_order(i, "load"), range(COUNT)) if r]
orders = [order_id for order_id, _ in results]
print(f"created={len(orders)}", flush=True)
settle(deadline, expected=orders)

with ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(lambda r: call(f"/admin/replay/{r[1]}", "POST"), results))
print(f"replayed={len(results)}", flush=True)

settle(deadline)
delivered, lost, duplicates = report(orders)
print(f"orders={len(orders)} in_warehouse={delivered} lost={lost} duplicates={duplicates}", flush=True)
