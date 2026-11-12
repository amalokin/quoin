import unittest

from svc.app import handle


class HandleTest(unittest.TestCase):
    def test_answers_the_health_probe_and_refuses_other_paths(self):
        self.assertEqual(handle({"method": "GET", "path": "/health"}), {"status": 200, "body": {"ok": True}})
        self.assertEqual(handle({"method": "GET", "path": "/missing"})["status"], 404)
