"""The rate feed.

``GET /v2/latest/<currency>`` answers ``{"currency": "USD", "rate":
"1.0832", "published": "2026-03-02"}``: how much of the currency one euro
buys, and the day the feed published it. The feed answers 404 for a currency
it does not carry and, when it is busy, 502, 503 or 504 for a moment.

There is no real feed in this repository. ``local_api`` starts a small
stand-in on 127.0.0.1. What it knows is in one JSON file: the day of its
rates, the rates, and for which currencies it is busy (how many calls).
"""

import json
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_TIMEOUT_SECONDS = 10


class FeedError(Exception):
    """The feed did not give a rate."""

    def __init__(self, currency, status):
        super().__init__(f"the feed answered {status} for {currency}")
        self.currency = currency
        self.status = status


def latest(base_url, currency):
    """Ask the feed for one currency. Returns (rate as text, day published)."""
    request = urllib.request.Request(
        f"{base_url}/v2/latest/{currency}", headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise FeedError(currency, error.code) from error
    return payload["rate"], payload["published"]


def _handler_for(state_path, lock):
    class FeedHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            prefix = "/v2/latest/"
            if not self.path.startswith(prefix):
                return self.send_error(404)
            currency = self.path[len(prefix):]
            with lock:
                with open(state_path, encoding="utf-8") as handle:
                    state = json.load(handle)
                busy = state.get("busy", {})
                if busy.get(currency, 0) > 0:
                    busy[currency] -= 1
                    if busy[currency] == 0:
                        del busy[currency]
                    with open(state_path, "w", encoding="utf-8") as handle:
                        handle.write(json.dumps(state, indent=2))
                    return self.send_error(503)
            if currency not in state["rates"]:
                return self.send_error(404)
            body = json.dumps({
                "currency": currency,
                "rate": state["rates"][currency],
                "published": state["published"],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass  # keep the job's output quiet

    return FeedHandler


@contextmanager
def local_api(state_path):
    """Run the stand-in feed on a free local port. Yields the base URL."""
    handler = _handler_for(state_path, threading.Lock())
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
