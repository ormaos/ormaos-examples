"""The carrier's rate API.

``GET /v1/rates?lane=EST-MID&kg=12.5&service=express`` with the header
``X-Account`` answers ``{"amount_cents": 4310, "currency": "EUR"}``. The
carrier refuses a call with 401 (unknown account), 404 (a lane it does not
serve), 422 (a weight it does not carry) or 429 (the account's calls for the
day are used up).

There is no real carrier in this repository. ``local_api`` starts a small
stand-in on 127.0.0.1. What it knows is in one JSON file: the account, its
calls per day and how many are used, and the carrier's tariff of today.
"""

import json
import os
import threading
import urllib.parse
import urllib.request
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_TIMEOUT_SECONDS = 10
MAX_KG = 1000
ACCOUNT = os.environ.get("FREIGHT_QUOTE_ACCOUNT", "WH-1001")


def rate(base_url, shipment):
    """Ask the carrier for the freight of one shipment. Returns cents."""
    query = urllib.parse.urlencode({
        "lane": shipment.lane,
        "kg": shipment.chargeable_kg,
        "service": shipment.service,
    })
    request = urllib.request.Request(
        f"{base_url}/v1/rates?{query}", headers={"X-Account": ACCOUNT}
    )
    with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
        payload = json.load(response)
    return int(payload["amount_cents"])


def tariff_price(tariff, lane, kg, service):
    """The carrier's price in cents, or None for a lane it does not serve."""
    if lane not in tariff["lanes"]:
        return None
    base_cents, per_kg_cents = tariff["lanes"][lane]
    cents = max(tariff["minimum_cents"], base_cents + per_kg_cents * kg)
    if service == "express":
        cents *= tariff["express_factor"]
    cents *= 1 + tariff["fuel_surcharge_percent"] / 100
    return round(cents)


def _handler_for(state_path, lock):
    class RatesHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlsplit(self.path)
            if url.path != "/v1/rates":
                return self.send_error(404)
            asked = dict(urllib.parse.parse_qsl(url.query))
            with lock:
                with open(state_path, encoding="utf-8") as handle:
                    state = json.load(handle)
                if self.headers.get("X-Account") != state["account"]:
                    return self.send_error(401)
                if state["calls_used_today"] >= state["calls_per_day"]:
                    return self.send_error(429)
                state["calls_used_today"] += 1
                with open(state_path, "w", encoding="utf-8") as handle:
                    handle.write(json.dumps(state, indent=2))
            kg = float(asked.get("kg", 0))
            if not 0 < kg <= MAX_KG:
                return self.send_error(422)
            cents = tariff_price(state["tariff"], asked.get("lane"), kg, asked.get("service"))
            if cents is None:
                return self.send_error(404)
            body = json.dumps({"amount_cents": cents, "currency": "EUR"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass  # keep the job's output quiet

    return RatesHandler


@contextmanager
def local_api(state_path):
    """Run the stand-in carrier on a free local port. Yields the base URL."""
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
