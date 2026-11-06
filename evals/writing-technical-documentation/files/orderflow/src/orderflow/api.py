"""HTTP API: create and read orders, and report health."""
import json
import logging
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from orderflow import config, store

log = logging.getLogger("orderflow.api")
ORDER_PATH = re.compile(r"^/orders/(\d+)$")
MAX_AMOUNT_CENTS = 1_000_000


class Handler(BaseHTTPRequestHandler):
    conn = None

    def _send(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            self._send(200, {"status": "ok", "queue_depth": store.queue_depth(self.conn)})
            return
        match = ORDER_PATH.match(self.path)
        order = store.get_order(self.conn, int(match.group(1))) if match else None
        if order is None:
            self._send(404, {"error": "not_found"})
            return
        self._send(200, order)

    def do_POST(self):
        if self.path != "/orders":
            self._send(404, {"error": "not_found"})
            return
        key = self.headers.get("Idempotency-Key")
        if not key:
            self._send(400, {"error": "missing_idempotency_key"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            amount = int(json.loads(self.rfile.read(length))["amount_cents"])
        except (ValueError, KeyError, TypeError):
            self._send(400, {"error": "invalid_amount"})
            return
        if not 0 < amount <= MAX_AMOUNT_CENTS:
            self._send(422, {"error": "amount_out_of_range"})
            return
        order_id, created = store.create_order(self.conn, amount, key)
        self._send(201 if created else 200, {"id": order_id, "status": store.PENDING})


def main():
    logging.basicConfig(level=logging.INFO)
    Handler.conn = store.connect(config.database_url())
    server = HTTPServer(("0.0.0.0", config.port()), Handler)
    log.info("listening on port %d", config.port())
    server.serve_forever()


if __name__ == "__main__":
    main()
