"""The only way out of an agent's container: an HTTP CONNECT proxy with a
list of hosts.

    python3 proxy.py --port 8080 --allow api.example.com:443 [--allow ...]

``CONNECT host:port`` is answered with a tunnel when ``host:port`` is on the
list, word for word (no wildcards, no subdomains), and with 403 otherwise.
Every other request (a plain ``GET http://...``) gets 403. One JSON line per
request goes to standard output: the time, the client, the target and
whether it was allowed.

Standard library only: the harness runs this file in a container of the base
image that stands on the agents' network and on the default one.
"""

import argparse
import json
import select
import socket
import socketserver
import sys
import time

LIMIT = 65536


def parse_target(target):
    """("host", port) of the target of a CONNECT, or None."""
    host, colon, port = target.rpartition(":")
    if not colon or not port.isdigit() or not host:
        return None
    return host.strip("[]").lower(), int(port)


class Handler(socketserver.StreamRequestHandler):
    timeout = 30

    def log(self, **facts):
        line = {"time": round(time.time(), 3), "client": self.client_address[0], **facts}
        with self.server.lock:
            self.server.out.write(json.dumps(line) + "\n")
            self.server.out.flush()

    def refuse(self, code, words, **facts):
        self.log(allowed=False, **facts)
        body = f"{words}\n".encode()
        self.wfile.write(f"HTTP/1.1 {code} {words}\r\nContent-Length: {len(body)}\r\n"
                         "Connection: close\r\n\r\n".encode() + body)

    def handle(self):
        try:
            first = self.rfile.readline(LIMIT).decode("latin-1").strip()
            while self.rfile.readline(LIMIT) not in (b"\r\n", b"\n", b""):
                pass  # the headers: nothing in them changes the answer
        except OSError:
            return
        parts = first.split()
        if len(parts) != 3:
            return
        method, target, _ = parts
        if method.upper() != "CONNECT":
            return self.refuse(403, "Only CONNECT", method=method, target=target[:200])
        where = parse_target(target)
        if where is None or f"{where[0]}:{where[1]}" not in self.server.allow:
            return self.refuse(403, "Host not allowed", method="CONNECT", target=target[:200])
        try:
            upstream = socket.create_connection(where, timeout=15)
        except OSError as error:
            return self.refuse(502, "Upstream failed", method="CONNECT", target=target, error=str(error))
        self.log(allowed=True, method="CONNECT", target=target)
        self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
        self.wfile.flush()
        relay(self.connection, upstream)


def relay(one, other):
    """Bytes in both directions until either side closes."""
    one.settimeout(None)
    other.settimeout(None)
    try:
        while True:
            ready, _, _ = select.select([one, other], [], [], 600)
            if not ready:
                return
            for source in ready:
                data = source.recv(LIMIT)
                if not data:
                    return
                (other if source is one else one).sendall(data)
    except OSError:
        return
    finally:
        other.close()


class Proxy(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, allow, out=sys.stdout):
        import threading

        self.allow = checked(allow)
        self.out = out
        self.lock = threading.Lock()
        super().__init__(address, Handler)


def checked(allow):
    """The list as a set of "host:port"; a wildcard or anything else that is
    not a plain host name is an error."""
    import re

    found = set()
    for entry in allow:
        entry = entry.lower()
        if not re.fullmatch(r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?:\d{1,5}", entry):
            raise ValueError(f"not a host:port (wildcards are not allowed): {entry!r}")
        found.add(entry)
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--allow", action="append", default=[], metavar="HOST:PORT")
    args = parser.parse_args(argv)
    with Proxy((args.host, args.port), args.allow) as server:
        print(json.dumps({"time": round(time.time(), 3), "listening": args.port,
                          "allow": sorted(server.allow)}), flush=True)
        server.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
