"""3. Same request: one task text per benchmark and arm, the same for every
agent, and no agent configuration in the task folder."""

import unittest

from support import Sandbox

import adapters
from benchmarks import knows2
from core import runner
from core.spec import Refused

BUILT = knows2.not_built(["order-sync"]) is None


class Config(Sandbox):
    def test_a_folder_with_agent_configuration_is_refused(self):
        for name in ("CLAUDE.md", "AGENTS.md", "GEMINI.md", "claude.md", ".mcp.json", ".cursorrules",
                     "sub/AGENTS.md", ".claude/settings.json", ".codex/config.toml", ".gemini/settings.json",
                     ".github/copilot-instructions.md", ".aider.conf.yml"):
            path = self.task / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x")
            batch = self.batch()
            with self.assertRaises(Refused, msg=name) as refused:
                batch.run()
            self.assertIn("agent configuration", str(refused.exception))
            self.assertEqual(self.runtime.commands, [], name)  # not even the canary ran
            path.unlink()
            for folder in (".claude", ".codex", ".gemini", ".github", "sub"):
                if (self.task / folder).is_dir():
                    (self.task / folder).rmdir()

    def test_a_plain_folder_is_not_refused(self):
        (self.task / "README.md").write_text("x")
        self.assertEqual(runner.agent_config(self.task), [])


class Text(Sandbox):
    def test_the_agent_gets_the_text_of_the_benchmark_unchanged(self):
        self.batch().run()
        run = next(c for c in self.runtime.commands if c["name"].endswith("t1-wrong-1"))
        self.assertEqual(run["argv"], ["zz", "Answer the question. (wrong)"])


@unittest.skipUnless(BUILT, "knows2 order-sync is not built")
class Knows2(unittest.TestCase):
    def test_the_texts_are_those_of_knows2(self):
        prompt = knows2.runner().tasks.prompt
        for arm in knows2.arms():
            text = knows2.text("order-sync", arm)
            self.assertEqual(text, prompt("order-sync", arm))
            for vendor in ("claude", "anthropic", "codex", "gemini", "grok"):
                self.assertNotIn(vendor, text.lower())
            argv = adapters.load("claude-code").argv(text, "m", "default")
            self.assertEqual(argv[-1], text)  # one argument, word for word

    def test_the_built_folders_hold_no_agent_configuration(self):
        for arm in knows2.arms():
            self.assertEqual(runner.agent_config(knows2.folder("order-sync", arm)), [])


if __name__ == "__main__":
    unittest.main()
