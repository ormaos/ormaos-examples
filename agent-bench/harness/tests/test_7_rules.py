"""7. Same rules: a run spec, expectations written before the run and not
changed after it, the first attempt of every slot, nothing run again."""

import json
import unittest

from support import AGENT, MODEL, HARNESS, FakeRuntime, Sandbox

from core import report, spec as specs
from core.spec import Refused


class Spec(Sandbox):
    def test_a_spec_names_benchmark_arms_agent_model_effort_n_and_time_limit(self):
        spec = specs.load(self.spec())
        self.assertEqual({key: spec[key] for key in specs.REQUIRED},
                         {"benchmark": "fakebench", "arms": ["right", "wrong"], "agent": AGENT, "model": MODEL,
                          "effort": "default", "n": 1, "time_limit_seconds": 20})
        path = self.spec(name="short")
        path.write_text(path.read_text().replace('effort = "default"\n', ""))
        with self.assertRaises(Refused):
            specs.load(path)
        with self.assertRaises(Refused):
            self.batch(spec=self.spec(name="odd", effort="enormous"))

    def test_the_runner_refuses_to_start_without_expectations(self):
        for text in (None, "  \n"):
            path = self.spec(name=f"none{text is None}", expectations=text)
            with self.assertRaises(Refused) as refused:
                self.batch(spec=path)
            self.assertIn("expectations/", str(refused.exception))

    def test_the_sha256_of_the_expectations_is_in_the_results(self):
        out = self.batch().run()
        run = json.loads((out / "run.json").read_text())
        expected = specs.sha256(self.root / "expectations" / "try.md")
        self.assertEqual(run["expectations"], {"file": "expectations/try.md", "sha256": expected})
        self.assertEqual(run["spec"]["name"], "try")
        self.assertIn(expected, (out / "report.md").read_text())

    def test_a_later_build_fails_when_the_expectations_changed(self):
        out = self.batch().run()
        report.write(out, self.root)  # unchanged: builds
        (self.root / "expectations" / "try.md").write_text("What I expect, now that I have seen it.\n")
        with self.assertRaises(Refused) as refused:
            report.write(out, self.root)
        self.assertIn("changed after the run started", str(refused.exception))
        (self.root / "expectations" / "try.md").unlink()
        with self.assertRaises(Refused):
            specs.verify(out, self.root)


class FirstAttempt(Sandbox):
    def test_every_slot_is_run_once_and_a_bad_run_counts(self):
        path = self.spec(arms=["right", "wrong", "crash"], n=2)
        out = self.batch(spec=path).run()
        records = self.results(out)
        self.assertEqual([(r["task"], r["arm"], r["run"]) for r in records],
                         [("t1", arm, run) for run in (1, 2) for arm in ("right", "wrong", "crash")])
        self.assertEqual([r["score"] for r in records], [1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        crashed = records[2]
        self.assertEqual((crashed["final"], crashed["exit_code"], crashed["answers"]), ("no_result", 3, None))
        runs = [c for c in self.runtime.commands if "-t1-" in c["name"]]
        self.assertEqual(len(runs), 6)  # no slot was run again

    def test_a_run_over_the_time_limit_is_stopped_and_counts(self):
        import subprocess

        runtime = FakeRuntime()
        started = []
        real = subprocess.Popen

        def popen(*args, **options):
            process = real(*args, **options)
            started.append(process)
            return process

        runtime.process_to_kill = lambda: started[-1].kill()
        subprocess.Popen = popen
        self.addCleanup(setattr, subprocess, "Popen", real)
        out = self.batch(spec=self.spec(arms=["sleep"], time_limit_seconds=2), runtime=runtime).run()
        record = self.results(out)[0]
        self.assertEqual((record["final"], record["timed_out"], record["score"]), ("time_limit", True, 0.0))
        self.assertLess(record["wall_seconds"], 10)

    def test_a_results_folder_is_not_written_twice(self):
        out = self.batch().run()
        again = self.batch(out=out)
        with self.assertRaises(Refused) as refused:
            again.run()
        self.assertIn("already has results", str(refused.exception))

    def test_a_dropped_or_doubled_result_fails_later_builds(self):
        out = self.batch().run()
        lines = (out / "results.jsonl").read_text().splitlines()
        (out / "results.jsonl").write_text(lines[0] + "\n")
        with self.assertRaises(Refused):
            specs.verify(out, self.root)
        (out / "results.jsonl").write_text("\n".join([*lines, lines[0]]) + "\n")
        with self.assertRaises(Refused):
            specs.verify(out, self.root)

    def test_the_results_are_where_and_what_knows2_has_plus_the_events(self):
        out = self.batch().run()
        self.assertEqual(out.relative_to(self.root).parts[:3], ("results", "fakebench", f"{AGENT}-{MODEL}"))
        self.assertRegex(out.name, r"^\d{8}-\d{6}$")
        have = {path.name for path in out.iterdir()}
        self.assertLessEqual({"build.json", "oracle", "report.md", "results.jsonl", "streams", "work",
                              "events", "run.json", "canary.txt", "expectations.md", "proxy.jsonl"}, have)
        record = self.results(out)[0]
        for key in ("task", "arm", "run", "score", "right", "answers", "answers_file", "wall_seconds", "timed_out",
                    "error", "tool_calls", "tools", "turns", "tokens", "cost_usd", "model", "started", "stream",
                    "folder"):  # the keys of a knows2 result
            self.assertIn(key, record)


class Committed(unittest.TestCase):
    def test_every_results_folder_in_the_repository_still_builds(self):
        """Fails when the expectations of a run were changed after it, when
        a planned run has no result, or when its events do not fit."""
        for run in sorted((HARNESS / "results").glob("*/*/*/run.json")):
            report.check(run.parent)


if __name__ == "__main__":
    unittest.main()
