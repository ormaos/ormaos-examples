"""The benchmark pages (site/benchmarks/build.py) read the results folders
of the harness: the expectations check, which run is shown, and its
environment."""

import importlib.util
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from support import HARNESS

REPO = HARNESS.parents[1]
SMOKE = HARNESS / "results" / "knows2" / "claude-code-claude-opus-5-5" / "20261127-192608"


def site():
    spec = importlib.util.spec_from_file_location("site_build", REPO / "site" / "benchmarks" / "build.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["site_build"] = module
    spec.loader.exec_module(module)
    return module


class Pages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = site()
        cls.scratch = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.shown, cls.tested = Path(cls.scratch.name) / "shown", Path(cls.scratch.name) / "tested"
        cls.build.build(cls.shown)
        cls.build.build(cls.tested, tests=True)

    def test_a_test_folder_is_not_shown_as_a_result(self):
        self.assertTrue((SMOKE / "TEST.md").exists())
        for page in self.shown.rglob("*.md"):
            self.assertNotIn(SMOKE.name, page.read_text(), page)

    def test_without_a_complete_harness_run_the_pages_show_the_earlier_run_and_name_its_environment(self):
        if any(r.complete and not r.test for r in self.harness_runs()):
            self.skipTest("there is a complete run made by the harness")
        overview = (self.shown / "benchmarks.md").read_text()
        self.assertIn('From the knows2 run of 2026-11-27, in the environment "earlier: bubblewrap, network open"',
                      overview)
        self.assertIn("agent-bench/knows2/results/20261127-165801", overview)
        knows2 = (self.shown / "benchmarks" / "knows2.md").read_text()
        self.assertIn("## The runs of knows2", knows2)
        self.assertIn("Environment: earlier: bubblewrap, network open", knows2)

    def harness_runs(self):
        h = self.build.runners()
        return [self.build.HarnessRun(folder, self.build.ARMS4, h)
                for folder in self.build.harness_folders(self.build.HARNESS_KNOWS2)]

    def test_a_complete_harness_run_gives_the_headline_and_the_knows2_page(self):
        """The smoke folder, counted as a run only here."""
        overview = (self.tested / "benchmarks.md").read_text()
        self.assertIn('in the environment "controlled: container, network limited to the model host"', overview)
        self.assertIn(f"agent-bench/harness/results/knows2/claude-code-claude-opus-5-5/{SMOKE.name}", overview)
        self.assertIn("answered 8 of 8 questions right, over its 1 runs; with only the folder (`none`), 1 of 8",
                      overview)
        knows2 = (self.tested / "benchmarks" / "knows2.md").read_text()
        self.assertIn("### The container", knows2)
        self.assertIn("a proxy that answers for `api.anthropic.com` and refuses every other host", knows2)
        self.assertIn("Environment: controlled: container, network limited to the model host", knows2)
        # both runs are listed, each with its environment
        runs = knows2[knows2.index("## The runs of knows2"):knows2.index("## This run")]
        self.assertIn("agent-bench/knows2/results/20261127-165801", runs)
        self.assertIn("earlier: bubblewrap, network open", runs)
        self.assertIn(SMOKE.name, runs)
        self.assertIn("this page", runs)

    def test_what_a_harness_run_did_is_read_from_its_events(self):
        case = (self.tested / "benchmarks" / "cases" / "knows2-order-sync.md").read_text()
        self.assertIn(f"{SMOKE.name}/events/order-sync-ormaos-1.jsonl", case)
        self.assertNotIn(f"{SMOKE.name}/streams/", case)
        run = next(r for r in self.harness_runs() if r.folder == SMOKE)
        record = next(r for r in run.records if r["arm"] == "ormaos")
        cwd, steps = self.build.steps_of(record)
        self.assertEqual((cwd, len(steps)), ("/srv/order-sync", record["tool_calls"]))
        self.assertIn("guide", self.build.verbs_before_answers(steps))

    def test_the_build_fails_when_the_expectations_of_a_harness_run_changed(self):
        expectations = HARNESS / "expectations" / "smoke.md"
        kept = expectations.read_text()
        self.addCleanup(expectations.write_text, kept)
        expectations.write_text(kept + "\nAnd the Ormaos arms score 1.00.\n")
        with self.assertRaises(SystemExit) as failed:
            self.build.build(Path(self.scratch.name) / "changed")
        self.assertIn("expectations/smoke.md changed after the run started", str(failed.exception))
        with self.assertRaises(SystemExit):
            self.build.main(["--check"])

    def test_an_unfinished_batch_is_not_shown(self):
        run = next(r for r in self.harness_runs() if r.folder == SMOKE)
        self.assertTrue(run.complete)
        copy = Path(self.scratch.name) / "half"
        shutil.copytree(SMOKE, copy)
        lines = (copy / "results.jsonl").read_text().splitlines()
        (copy / "results.jsonl").write_text("\n".join(lines[:2]) + "\n")
        h = self.build.runners()
        half = self.build.HarnessRun.__new__(self.build.HarnessRun)
        with unittest.mock.patch.object(self.build, "added_in", lambda path: "0" * 40):
            half.__init__(copy, self.build.ARMS4, h)
        self.assertFalse(half.complete)


if __name__ == "__main__":
    unittest.main()
