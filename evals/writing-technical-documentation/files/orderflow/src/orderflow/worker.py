"""Payment worker: charges pending orders one at a time, with retries."""
import logging
import time
import urllib.error
import urllib.request

from orderflow import config, store

log = logging.getLogger("orderflow.worker")
PAYMENTS_URL = "https://payments.example.com/v1/charges"
BASE_DELAY_SECONDS = 0.2
MAX_DELAY_SECONDS = 5.0
POLL_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 10


class PaymentError(Exception):
    """The payment provider refused the charge or could not be reached."""


def charge(order):
    request = urllib.request.Request(
        PAYMENTS_URL,
        data=str(order["amount_cents"]).encode(),
        headers={"Authorization": "Bearer " + config.payments_api_key()},
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS):
            return
    except (urllib.error.URLError, TimeoutError) as exc:
        raise PaymentError(str(exc)) from exc


def backoff_delay(attempt):
    """Seconds to wait after a failed attempt: 0.2, 0.4, 0.8, capped at 5."""
    return min(BASE_DELAY_SECONDS * (2 ** (attempt - 1)), MAX_DELAY_SECONDS)


def process(conn, order, charge_fn=charge, sleep=time.sleep):
    """Try to charge one order. After WORKER_MAX_RETRIES failures it goes to the dead letter state."""
    limit = config.max_retries()
    error = None
    for attempt in range(1, limit + 1):
        try:
            charge_fn(order)
            store.mark(conn, order["id"], store.PAID, attempt)
            log.info("order.paid id=%s attempts=%d", order["id"], attempt)
            return store.PAID
        except PaymentError as exc:
            error = str(exc)
            log.warning("order.retry id=%s attempt=%d error=%s", order["id"], attempt, error)
            sleep(backoff_delay(attempt))
    store.mark(conn, order["id"], store.DEAD, limit, error)
    log.error("order.failed id=%s attempts=%d error=%s", order["id"], limit, error)
    return store.DEAD


def check_backlog(conn):
    depth = store.queue_depth(conn)
    if depth > config.backlog_alert():
        log.error("queue.backlog depth=%d threshold=%d", depth, config.backlog_alert())
    return depth


def main():
    logging.basicConfig(level=logging.INFO)
    conn = store.connect(config.database_url())
    while True:
        check_backlog(conn)
        order = store.next_pending(conn)
        if order is None:
            time.sleep(POLL_SECONDS)
            continue
        process(conn, order)


if __name__ == "__main__":
    main()
