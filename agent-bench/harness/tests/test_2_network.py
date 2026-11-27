"""2. Same network: no way out but a CONNECT proxy with a list of hosts, and
a canary before the batch."""

import io
import socket
import subprocess
import sys
import threading
import unittest

from support import HARNESS, HAVE_RUNTIME, Sandbox, FakeRuntime

import adapters
from core import proxy
from core.spec import Refused


def ask(port, request):
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        client.sendall(request)
        client.settimeout(5)
        return client.recv(4096)


class Proxy(unittest.TestCase):
    def setUp(self):
        self.echo = socket.create_server(("127.0.0.1", 0))
        self.addCleanup(self.echo.close)
        self.target = self.echo.getsockname()[1]

        def serve():
            try:
                peer, _ = self.echo.accept()
                peer.sendall(b"hello " + peer.recv(100))
                peer.close()
            except OSError:
                pass

        threading.Thread(target=serve, daemon=True).start()
        self.log = io.StringIO()
        self.server = proxy.Proxy(("127.0.0.1", 0), [f"localhost:{self.target}"], out=self.log)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.port = self.server.server_address[1]

    def test_a_listed_host_gets_a_tunnel(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=5) as client:
            client.sendall(f"CONNECT localhost:{self.target} HTTP/1.1\r\nHost: x\r\n\r\n".encode())
            client.settimeout(5)
            self.assertTrue(client.recv(4096).startswith(b"HTTP/1.1 200"))
            client.sendall(b"there")
            self.assertEqual(client.recv(100), b"hello there")
        self.assertIn('"allowed": true', self.log.getvalue())

    def test_any_other_host_is_refused(self):
        for target in (f"127.0.0.1:{self.target}", f"sub.localhost:{self.target}", "localhost:1",
                       "github.com:443", "raw.githubusercontent.com:443", "nonsense"):
            answer = ask(self.port, f"CONNECT {target} HTTP/1.1\r\n\r\n".encode())
            self.assertTrue(answer.startswith(b"HTTP/1.1 403"), (target, answer))
        self.assertEqual(self.log.getvalue().count('"allowed": false'), 6)

    def test_a_request_that_is_not_connect_is_refused(self):
        answer = ask(self.port, f"GET http://localhost:{self.target}/ HTTP/1.1\r\n\r\n".encode())
        self.assertTrue(answer.startswith(b"HTTP/1.1 403"))

    def test_no_wildcards(self):
        for entry in ("*.anthropic.com:443", "*:443", "anthropic.com", ".anthropic.com:443"):
            with self.assertRaises(ValueError):
                proxy.checked([entry])


class Hosts(unittest.TestCase):
    def test_claude_code_lists_plain_hosts_of_its_vendor(self):
        adapter = adapters.load("claude-code")
        self.assertEqual(adapter.hosts, ("api.anthropic.com",))
        self.assertNotIn("github", " ".join(adapter.hosts))

    def test_an_adapter_with_a_wildcard_does_not_load(self):
        from support import FakeAdapter

        class Wide(FakeAdapter):
            hosts = ("*.example.com",)

        with self.assertRaises(ValueError):
            adapters.check(Wide())


class Canary(Sandbox):
    def test_the_batch_does_not_start_when_the_canary_fails(self):
        runtime = FakeRuntime(canary="PASS blocked: a\nFAIL reached: https://github.com (HTTP 200)")
        batch = self.batch(runtime=runtime)
        with self.assertRaises(Refused) as refused:
            batch.run()
        self.assertIn("FAIL reached: https://github.com", str(refused.exception))
        self.assertEqual([c["argv"][0] for c in runtime.commands], ["harness-canary"])  # no agent ran
        self.assertFalse(batch.out.exists())
        self.assertEqual((runtime.up, runtime.down), (1, 1))

    def test_the_canary_runs_before_every_batch_and_is_kept(self):
        out = self.batch().run()
        self.assertEqual(self.runtime.commands[0]["argv"][:2], ["harness-canary", "https://model.example.com/"])
        self.assertIn("PASS reached: the model", (out / "canary.txt").read_text())
        self.assertIn("PASS model:", (out / "canary.txt").read_text())

    def test_every_run_is_sent_through_the_proxy(self):
        self.batch().run()
        for command in self.runtime.commands:
            self.assertEqual(command["env"]["HTTPS_PROXY"], "http://127.0.0.1:9")
            self.assertEqual(command["env"]["https_proxy"], "http://127.0.0.1:9")


@unittest.skipUnless(HAVE_RUNTIME, "needs podman or docker")
class RealCanary(unittest.TestCase):
    def test_github_is_blocked_and_the_model_host_answers(self):
        done = subprocess.run([sys.executable, str(HARNESS / "harness.py"), "canary", "claude-code"],
                              capture_output=True, text=True, timeout=600)
        said = done.stdout
        self.assertEqual(done.returncode, 0, said + done.stderr)
        self.assertIn("PASS blocked: https://github.com through the proxy", said)
        self.assertIn("PASS blocked: https://raw.githubusercontent.com through the proxy", said)
        self.assertIn("PASS blocked: https://github.com without the proxy", said)
        self.assertIn("PASS reached: https://api.anthropic.com/ through the proxy", said)
        self.assertNotIn("FAIL", said)


if __name__ == "__main__":
    unittest.main()
