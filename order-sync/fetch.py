"""Get the raw orders from the sales system.

Two sources:

- a CSV export (the default), one order per line;
- the sales API, which answers ``GET /orders`` with a JSON list.

There is no real sales API in this repository. ``local_api`` starts a small
stand-in on 127.0.0.1 that serves the same orders from the CSV export.
"""

import csv
import json
import threading
import urllib.request
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_TIMEOUT_SECONDS = 10


def from_csv(path):
    """Read the CSV export. Returns a list of dicts, one per order."""
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def from_api(base_url):
    """Ask the sales API for the orders. Returns a list of dicts."""
    url = f"{base_url}/orders"
    with urllib.request.urlopen(url, timeout=API_TIMEOUT_SECONDS) as response:
        payload = json.load(response)
    return payload["orders"]


def _handler_for(csv_path):
    class OrdersHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/orders":
                self.send_error(404)
                return
            body = json.dumps({"orders": from_csv(csv_path)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass  # keep the job's output quiet

    return OrdersHandler


@contextmanager
def local_api(csv_path):
    """Serve the CSV export over HTTP on a free local port. Yields the base URL."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(csv_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
