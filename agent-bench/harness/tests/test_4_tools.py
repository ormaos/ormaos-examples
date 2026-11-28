"""4. Same tools: shell and file edits only, and a new home folder that
holds the agent's credential and nothing else."""

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from support import HAVE_RUNTIME, SECRET, FakeRuntime, Sandbox

import adapters
from core import runner
from core import runtime as runtimes


class ClaudeCode(unittest.TestCase):
    def setUp(self):
        self.adapter = adapters.load("claude-code")
        self.argv = self.adapter.argv("text", "claude-opus-5-5", "default")

    def test_the_tools_are_shell_and_files(self):
        tools = self.argv[self.argv.index("--tools") + 1].split(",")
        self.assertEqual(tools, ["Bash", "Read", "Grep", "Glob", "Edit", "Write"])
        self.assertEqual(self.argv[self.argv.index("--allowedTools") + 1].split(","), tools)
        self.assertEqual(set(self.adapter.tools.values()), {"shell", "file"})
        for tool in ("WebSearch", "WebFetch", "Task", "Agent", "Skill"):
            self.assertNotIn(tool, tools)

    def test_no_mcp_no_customizations_no_memory(self):
        for flag in ("--strict-mcp-config", "--safe-mode", "--no-session-persistence"):
            self.assertIn(flag, self.argv)
        self.assertNotIn("--mcp-config", self.argv)
        self.assertEqual(self.adapter.env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"], "1")

    def test_effort_is_passed_when_the_spec_names_one(self):
        self.assertNotIn("--effort", self.argv)
        argv = self.adapter.argv("text", "m", "high")
        self.assertEqual(argv[argv.index("--effort") + 1], "high")

    def test_the_home_gets_only_the_login_without_refresh_token_and_other_tokens(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "me"
            (source / ".claude").mkdir(parents=True)
            (source / ".claude" / "settings.json").write_text("{}")
            (source / ".claude" / ".credentials.json").write_text(json.dumps({
                "claudeAiOauth": {"accessToken": "at-1", "refreshToken": "rt-1", "expiresAt": 4102444800000,
                                  "scopes": ["user:inference"], "subscriptionType": "max"},
                "mcpOAuth": {"other-service": {"accessToken": "mcp-1"}},
            }))
            home = runner.new_home(self.adapter, source, scratch)
            files = sorted(str(p.relative_to(home)) for p in home.rglob("*") if p.is_file())
            self.assertEqual(files, [".claude/.credentials.json"])
            path = home / files[0]
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
            kept = json.loads(path.read_text())
            self.assertEqual(list(kept), ["claudeAiOauth"])
            self.assertEqual(kept["claudeAiOauth"]["accessToken"], "at-1")
            self.assertNotIn("refreshToken", kept["claudeAiOauth"])
            self.assertNotIn("mcp-1", path.read_text())
            self.assertEqual(self.adapter.secrets(source), ["at-1", "rt-1"])
            self.assertGreater(self.adapter.credential_seconds(source), 0)


class Violations(Sandbox):
    def test_the_batch_does_not_start_when_the_agent_has_another_tool(self):
        """The last check of the canary is the agent itself: what it starts
        with is compared with the tools of its adapter."""
        from core.spec import Refused

        runtime = FakeRuntime(tools=("sh", "edit", "web_search"))
        batch = self.batch(runtime=runtime)
        with self.assertRaises(Refused) as refused:
            batch.run()
        self.assertIn("FAIL model:", str(refused.exception))
        self.assertIn("tools beyond shell and files: web_search", str(refused.exception))
        self.assertEqual(len(runtime.commands), 2)  # the canary and its model check; no run
        self.assertFalse(batch.out.exists())

    def test_a_printed_credential_is_removed_and_reported(self):
        out = self.batch(runtime=FakeRuntime(says=SECRET)).run()
        for path in list((out / "streams").iterdir()) + list((out / "events").iterdir()):
            self.assertNotIn(SECRET, path.read_text())
        self.assertIn("the agent printed its credential", self.results(out)[0]["violations"][0])

    def test_the_home_of_every_run_is_new_and_removed(self):
        out = self.batch().run()
        homes = [next(source for source, inside, _ in c["mounts"] if inside == runner.HOME_INSIDE)
                 for c in self.runtime.commands]
        self.assertEqual(len(set(homes)), len(homes))
        self.assertFalse(any(Path(home).exists() for home in homes))
        self.assertTrue(out.exists())


@unittest.skipUnless(HAVE_RUNTIME, "needs podman or docker")
class Listing(unittest.TestCase):
    def test_a_run_that_lists_its_home_sees_only_the_credential(self):
        """The home folder and the command line of a run, with `find ~` in
        the place of the agent."""
        adapter, runtime = adapters.load("claude-code"), runtimes.Runtime()
        _, agent = runtime.images(adapter)
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "me"
            (source / ".claude").mkdir(parents=True)
            (source / ".claude" / ".credentials.json").write_text(json.dumps(
                {"claudeAiOauth": {"accessToken": "at-1", "refreshToken": "rt-1"}, "mcpOAuth": {"x": 1}}))
            (source / ".ssh").mkdir()
            (source / ".ssh" / "id_ed25519").write_text("not for the agent")
            home = runner.new_home(adapter, source, scratch)
            command = runtime.command(f"ormaos-harness-test-{os.getpid()}", agent["tag"], "none",
                                      {"HOME": runner.HOME_INSIDE}, [(home, runner.HOME_INSIDE, "rw")], "/tmp",
                                      ["bash", "-c", "cd ~ && find . -mindepth 1 | sort; cat .claude/.credentials.json; "
                                                     "echo; echo x 2>/dev/null >> .claude/.credentials.json || echo read-only"])
            import subprocess

            said = subprocess.run(command, capture_output=True, text=True, timeout=120).stdout.splitlines()
        self.assertEqual(said[:2], ["./.claude", "./.claude/.credentials.json"])
        self.assertEqual(json.loads(said[2]), {"claudeAiOauth": {"accessToken": "at-1"}})
        self.assertEqual(said[3:], ["read-only"])


if __name__ == "__main__":
    unittest.main()
