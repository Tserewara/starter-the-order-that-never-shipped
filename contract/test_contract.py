"""Checkout's given behaviour, black-box. A port passes these."""

import os
import time
import unittest

import httpx
import psycopg

SERVICE = os.environ.get("SERVICE_URL", "http://localhost:8000")
WAREHOUSE_URL = os.environ.get("WAREHOUSE_URL", "postgresql://warehouse:warehouse@localhost:5432/warehouse")


def picks_for(order_id):
    with psycopg.connect(WAREHOUSE_URL) as conn:
        return conn.execute("SELECT count(*) FROM picks WHERE order_id = %s", (order_id,)).fetchone()[0]


def eventually(check, seconds=15):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if check():
            return True
        time.sleep(0.2)
    return False


class Contract(unittest.TestCase):
    def test_health(self):
        self.assertEqual(httpx.get(f"{SERVICE}/health").status_code, 200)

    def test_order_reaches_the_warehouse(self):
        r = httpx.post(f"{SERVICE}/orders", json={"customer": "ana", "sku": "tea-42"})
        self.assertIn(r.status_code, (201, 202))
        body = r.json()
        self.assertTrue(body["order_id"] and body["event_id"])
        self.assertTrue(eventually(lambda: picks_for(body["order_id"]) >= 1))

    def test_replay_of_an_unknown_event_is_404(self):
        self.assertEqual(httpx.post(f"{SERVICE}/admin/replay/nope").status_code, 404)

    def test_replay_of_a_known_event(self):
        body = httpx.post(f"{SERVICE}/orders", json={"customer": "sam"}).json()
        self.assertEqual(httpx.post(f"{SERVICE}/admin/replay/{body['event_id']}").status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
