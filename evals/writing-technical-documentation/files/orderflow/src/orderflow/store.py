"""SQLite storage for orders. The orders table doubles as the worker's queue."""
import sqlite3

PENDING, PAID, DEAD = "pending", "paid", "dead"

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT UNIQUE,
    amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
)
"""


def connect(url):
    conn = sqlite3.connect(url)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def create_order(conn, amount_cents, idempotency_key):
    """Insert an order, or return the existing one for a repeated Idempotency-Key."""
    existing = conn.execute("SELECT id FROM orders WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
    if existing:
        return existing["id"], False
    cur = conn.execute("INSERT INTO orders (idempotency_key, amount_cents) VALUES (?, ?)", (idempotency_key, amount_cents))
    conn.commit()
    return cur.lastrowid, True


def get_order(conn, order_id):
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return dict(row) if row else None


def queue_depth(conn):
    return conn.execute("SELECT COUNT(*) AS n FROM orders WHERE status = ?", (PENDING,)).fetchone()["n"]


def dead_letter_count(conn):
    return conn.execute("SELECT COUNT(*) AS n FROM orders WHERE status = ?", (DEAD,)).fetchone()["n"]


def next_pending(conn):
    row = conn.execute("SELECT * FROM orders WHERE status = ? ORDER BY id LIMIT 1", (PENDING,)).fetchone()
    return dict(row) if row else None


def mark(conn, order_id, status, attempts, error=None):
    conn.execute("UPDATE orders SET status = ?, attempts = ?, last_error = ? WHERE id = ?", (status, attempts, error, order_id))
    conn.commit()


def requeue_dead(conn, limit=None):
    """Move dead-letter orders back to pending and reset their attempts. Returns the count."""
    ids = [r["id"] for r in conn.execute("SELECT id FROM orders WHERE status = ? ORDER BY id", (DEAD,))]
    ids = ids[:limit] if limit else ids
    for order_id in ids:
        mark(conn, order_id, PENDING, 0)
    return len(ids)
