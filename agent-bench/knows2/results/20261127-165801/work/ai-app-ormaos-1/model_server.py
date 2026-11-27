"""A stand-in for a model API, for local runs: it answers on 127.0.0.1.

    POST /v1/models/<model>/generate    {"prompt": "..."}  ->  {"model": ..., "text": ...}

`small-1` takes prompts of up to 600 characters and answers 503 to a longer
one; `large-1` takes any prompt. No model runs: the text is the first
sentence of the prompt's last paragraph.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LIMITS = {"small-1": 600, "large-1": None}


def generate(model, prompt):
    if model not in LIMITS:
        return 404, {"error": "no such model"}
    limit = LIMITS[model]
    if limit is not None and len(prompt) > limit:
        return 503, {"error": "model overloaded"}
    last = prompt.strip().split("\n")[-1]
    return 200, {"model": model, "text": last.split(". ")[0].rstrip(".") + "."}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parts = self.path.strip("/").split("/")
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if len(parts) == 4 and parts[:2] == ["v1", "models"] and parts[3] == "generate":
            status, answer = generate(parts[2], body["prompt"])
        else:
            status, answer = 404, {"error": "no such route"}
        self.reply(status, answer)

    def reply(self, code, answer):
        data = json.dumps(answer).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def start():
    """Start the server on a free port; give it back with its address."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"
