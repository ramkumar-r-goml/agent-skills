import unittest

from orderflow import store


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.conn = store.connect(":memory:")

    def test_repeated_idempotency_key_returns_existing_order(self):
        first, created = store.create_order(self.conn, 500, "abc")
        second, created_again = store.create_order(self.conn, 500, "abc")
        self.assertEqual(first, second)
        self.assertTrue(created)
        self.assertFalse(created_again)

    def test_requeue_dead_resets_attempts(self):
        order_id, _ = store.create_order(self.conn, 500, "abc")
        store.mark(self.conn, order_id, store.DEAD, 3, "timeout")
        self.assertEqual(store.requeue_dead(self.conn), 1)
        self.assertEqual(store.get_order(self.conn, order_id)["attempts"], 0)


if __name__ == "__main__":
    unittest.main()
