"""1. Same environment: one base image pinned by digest, one layer per agent
with only its command line, and the image ids in every result."""

import re
import unittest

from support import HARNESS, HAVE_RUNTIME, Sandbox

import adapters
from core import runtime as runtimes


class Files(unittest.TestCase):
    def test_base_is_pinned_by_digest(self):
        froms = re.findall(r"^FROM (\S+)", (HARNESS / "image" / "Containerfile").read_text(), re.M)
        self.assertEqual(len(froms), 2)
        for image in froms:
            self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")
        self.assertTrue(froms[-1].startswith("ubuntu:"))

    def test_an_agent_adds_one_layer_with_a_pinned_command_line(self):
        adapter = adapters.load("claude-code")
        lines = [line.split()[0] for line in adapter.containerfile.read_text().splitlines()
                 if line and not line.startswith(("#", " "))]
        self.assertEqual(lines, ["ARG", "FROM", "ARG", "ARG", "RUN"])
        self.assertIn("FROM ${BASE}", adapter.containerfile.read_text())
        self.assertRegex(adapter.cli_version, r"^\d+\.\d+\.\d+$")
        self.assertRegex(adapter.build_args["CLI_SHA256"], r"^[0-9a-f]{64}$")


@unittest.skipUnless(HAVE_RUNTIME, "needs podman or docker")
class Images(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = runtimes.Runtime()
        cls.adapter = adapters.load("claude-code")
        cls.base, cls.agent = cls.runtime.images(cls.adapter)

    def test_the_agent_image_is_the_base_and_one_layer(self):
        self.assertEqual(self.agent["layers"][:-1], self.base["layers"])
        self.assertEqual(len(self.agent["layers"]), len(self.base["layers"]) + 1)

    def test_the_base_has_ubuntu_python_and_uv_and_no_agent(self):
        said = self.runtime.do("run", "--rm", self.base["tag"], "bash", "-c",
                               ". /etc/os-release; echo $ID; python3 --version; uv --version; "
                               "command -v claude codex gemini grok || echo no-agent").stdout.split("\n")
        self.assertEqual(said[0], "ubuntu")
        self.assertRegex(said[1], r"^Python 3\.\d+")
        self.assertRegex(said[2], r"^uv 0\.13\.5")
        self.assertEqual(said[3], "no-agent")

    def test_the_agent_image_has_the_pinned_version(self):
        said = self.runtime.do("run", "--rm", self.agent["tag"], "claude", "--version").stdout
        self.assertTrue(said.startswith(self.adapter.cli_version), said)


class Results(Sandbox):
    def test_every_result_records_the_image_ids(self):
        out = self.batch().run()
        for record in self.results(out):
            self.assertEqual(record["images"], {"base": "sha256:base", "agent": "sha256:agent"})

    def test_the_task_folder_is_mounted_at_srv_task(self):
        self.batch().run()
        run = next(c for c in self.runtime.commands if c["name"].endswith("t1-right-1"))
        self.assertEqual(run["workdir"], "/srv/t1")
        self.assertIn(("/srv/t1", "rw"), [(inside, mode) for _, inside, mode in run["mounts"]])

    def test_a_python_other_than_the_tasks_is_refused(self):
        from core.spec import Refused

        self.modules["benchmarks.fakebench"].python = lambda: "3.12"
        with self.assertRaises(Refused):
            self.batch().run()


if __name__ == "__main__":
    unittest.main()
