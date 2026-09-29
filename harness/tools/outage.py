"""Tuesday, small. `make outage` pauses the broker, runs `outage.py create`,
resumes the broker and runs `outage.py check`.

    create   100 orders while the broker is paused; their ids go to /work
    check    waits for the warehouse feed to settle, then counts
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from common import create_order, report, settle

STATE = "/work/outage.json"

if sys.argv[1] == "create":
    with ThreadPoolExecutor(max_workers=25) as pool:
        results = list(pool.map(lambda i: create_order(i, "outage"), range(100)))
    accepted = [r[0] for r in results if r]
    json.dump(accepted, open(STATE, "w"))
    print(f"created=100 accepted={len(accepted)} (broker paused)", flush=True)
else:
    accepted = json.load(open(STATE))
    settle(time.time() + 120, expected=accepted)
    delivered, lost, duplicates = report(accepted)
    print(f"accepted={len(accepted)} in_warehouse={delivered} lost={lost} duplicates={duplicates}", flush=True)
