"""A credential that is about to expire: the batch stops before the next
run, and continuing it starts only the runs that never started."""

import json
import sys

from support import Sandbox

from core import report, runner, spec as specs
from core.spec import Refused

LONG, SHORT = 5000, runner.MARGIN - 1


class Expiring(Sandbox):
    def setUp(self):
        super().setUp()
        self.adapter = sys.modules["adapters.zzagent"].ADAPTER
        self.said = []
        self.path = self.spec(n=2)  # four slots: right and wrong, twice

    def start(self, lefts, **options):
        self.adapter.lefts = lefts
        batch = self.batch(spec=self.path, **options)
        batch.say = self.said.append
        return batch

    def slots(self, runtime):
        return [c["name"].split("-t1-")[1] for c in runtime.commands if "-t1-" in c["name"]]

    def test_a_batch_does_not_start_with_a_credential_that_expires_within_20_minutes(self):
        self.assertEqual(runner.MARGIN, 20 * 60)
        with self.assertRaises(Refused) as refused:
            self.start([SHORT]).run()
        self.assertIn("zz login", str(refused.exception))
        self.assertEqual(list((self.root / "results").iterdir()), [])
        self.start([runner.MARGIN + 1]).run()  # one second more: it starts

    def test_the_batch_stops_before_the_run_and_the_rest_is_not_started(self):
        # the check at the start, before run 1, before run 2, then before run 3
        out = self.start([LONG, LONG, LONG, SHORT]).run()
        self.assertEqual(self.slots(self.runtime), ["right-1", "wrong-1"])
        self.assertEqual([(r["arm"], r["run"]) for r in self.results(out)], [("right", 1), ("wrong", 1)])
        run = json.loads((out / "run.json").read_text())
        self.assertIsNone(run["finished"])
        self.assertEqual(run["stops"][0]["before"], ["t1", "right", 2])
        self.assertEqual(run["stops"][0]["credential_seconds"], SHORT)
        for slot in ("t1-right-2", "t1-wrong-2"):  # they never started: nothing of them is there
            self.assertFalse((out / "work" / slot).exists())
            self.assertFalse((out / "events" / f"{slot}.jsonl").exists())
        text = (out / "report.md").read_text()
        self.assertIn("4 runs planned, 2 run", text)
        self.assertEqual(text.count("not started (the batch stopped before it; it is not a failure"), 2)
        specs.verify(out, self.root)  # not a failure: the folder still builds
        report.check(out, self.root)
        said = "\n".join(self.said)
        self.assertIn("stopped before t1, right, run 2", said)
        self.assertIn("renew the credential:  zz login", said)
        self.assertIn(f"python3 harness.py run specs/try.toml --continue {out.relative_to(self.root)}", said)

    def test_continuing_starts_only_the_runs_that_never_started(self):
        out = self.start([LONG, LONG, LONG, SHORT]).run()
        first = self.results(out)
        again = self.start([], out=out, resume=True)
        self.assertEqual(again.run(), out)
        self.assertEqual(self.slots(self.runtime), ["right-2", "wrong-2"])  # and no slot a second time
        records = self.results(out)
        self.assertEqual(records[:2], first)  # what was there is as it was
        self.assertEqual([(r["arm"], r["run"]) for r in records],
                         [("right", 1), ("wrong", 1), ("right", 2), ("wrong", 2)])
        run = json.loads((out / "run.json").read_text())
        self.assertTrue(run["finished"])
        self.assertEqual((len(run["stops"]), len(run["continued"])), (1, 1))
        self.assertIn("continued", (out / "canary.txt").read_text())  # the canary ran again
        text = (out / "report.md").read_text()
        self.assertIn("4 runs planned, 4 run", text)
        self.assertNotIn("not started (", text)
        report.check(out, self.root)

    def test_a_batch_can_stop_and_be_continued_more_than_once(self):
        out = self.start([LONG, LONG, SHORT]).run()
        self.start([LONG, LONG, SHORT], out=out, resume=True).run()
        self.assertEqual(len(self.results(out)), 2)
        self.start([], out=out, resume=True).run()
        self.assertEqual(sorted((r["arm"], r["run"]) for r in self.results(out)),
                         [("right", 1), ("right", 2), ("wrong", 1), ("wrong", 2)])
        self.assertEqual(len(json.loads((out / "run.json").read_text())["stops"]), 2)

    def test_a_run_that_started_and_left_no_result_is_not_run_again(self):
        out = self.start([LONG, LONG, LONG, SHORT]).run()
        (out / "work" / "t1-right-2").mkdir()  # as a run that was cut off leaves it
        with self.assertRaises(Refused) as refused:
            self.start([], out=out, resume=True).run()
        self.assertEqual(self.slots(self.runtime), ["wrong-2"])
        self.assertIn("without a result", str(refused.exception))

    def test_only_the_same_batch_is_continued(self):
        out = self.start([LONG, LONG, LONG, SHORT]).run()
        with self.assertRaises(Refused):  # no folder named
            self.start([], resume=True)
        (self.root / "expectations" / "try.md").write_text("Now that I have seen half of it.\n")
        with self.assertRaises(Refused) as refused:
            self.start([], out=out, resume=True).run()
        self.assertIn("changed after the run started", str(refused.exception))
        (self.root / "expectations" / "try.md").write_text("What I expect.\n")
        self.path.write_text(self.path.read_text().replace("n = 2", "n = 3"))
        with self.assertRaises(Refused) as refused:
            self.start([], out=out, resume=True).run()
        self.assertIn("not the spec this batch started with", str(refused.exception))
        self.path.write_text(self.path.read_text().replace("n = 3", "n = 2"))
        self.start([], out=out, resume=True).run()
        with self.assertRaises(Refused) as refused:  # finished: nothing to continue
            self.start([], out=out, resume=True).run()
        self.assertIn("is finished", str(refused.exception))


class TestRuns(Sandbox):
    def test_a_spec_that_says_test_marks_its_results_folder(self):
        out = self.batch(spec=self.spec(name="trial", test=True)).run()
        self.assertTrue((out / runner.TEST).exists())
        self.assertIn("A test of the harness, not a result", (out / "report.md").read_text())
        self.assertFalse((self.batch(spec=self.spec(name="real"), out=self.root / "results" / "real").run() / runner.TEST).exists())
