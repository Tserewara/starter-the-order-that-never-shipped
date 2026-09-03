import json
import os
import urllib.request
import unittest


BASE = os.environ.get("TEST_URL", "http://localhost:8000")


def call(path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(BASE + path, data=body, method=method)
    if body:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read())


class GivenBehaviourTests(unittest.TestCase):
    def test_health(self):
        status, value = call("/health")
        self.assertEqual(status, 200)
        self.assertEqual(value["status"], "ok")

    def test_order_is_accepted(self):
        status, value = call("/orders", "POST", {"customer": "Mara", "sku": "tea-42"})
        self.assertIn(status, (201, 202))
        self.assertTrue(value["order_id"])
        self.assertTrue(value["event_id"])


if __name__ == "__main__":
    unittest.main()
