import unittest

from orderflow import store, worker


class WorkerTest(unittest.TestCase):
    def setUp(self):
        self.conn = store.connect(":memory:")
        order_id, _ = store.create_order(self.conn, 500, "abc")
        self.order = store.get_order(self.conn, order_id)

    def test_order_goes_dead_after_three_failures(self):
        calls = []

        def always_fails(order):
            calls.append(order["id"])
            raise worker.PaymentError("timeout")

        self.assertEqual(worker.process(self.conn, self.order, always_fails, lambda s: None), store.DEAD)
        self.assertEqual(len(calls), 3)

    def test_backoff_doubles_and_caps_at_five_seconds(self):
        self.assertEqual(worker.backoff_delay(1), 0.2)
        self.assertEqual(worker.backoff_delay(2), 0.4)
        self.assertEqual(worker.backoff_delay(9), 5.0)


if __name__ == "__main__":
    unittest.main()
