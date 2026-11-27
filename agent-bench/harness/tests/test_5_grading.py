"""5. Same grading: outside the container, by the oracle and the rules the
benchmark already has, by a grader that is not told who ran."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import AGENT, MODEL, Sandbox

from benchmarks import knows2
from core import grading

BUILT = knows2.not_built(["order-sync"]) is None


class Blind(Sandbox):
    def test_the_grader_gets_the_task_and_the_folder_and_nothing_of_the_agent(self):
        seen = []

        def grader(benchmark, task, work, oracle_file):
            real = subprocess.run

            def spy(argv, **options):
                seen.append((argv, options))
                return mock.Mock(returncode=0, stdout='{"score": 1.0, "right": {"q1": true}, "answers": {"q1": 1}, '
                                                      '"answers_file": "read"}', stderr="")

            with mock.patch.object(grading.subprocess, "run", spy):
                return grading.blind(benchmark, task, work, oracle_file)
            del real

        out = self.batch(grader=grader).run()
        self.assertIn(f"{AGENT}-{MODEL}", str(out))  # the results do say who ran
        self.assertEqual(len(seen), 2)
        for argv, options in seen:
            told = json.dumps([argv, options["cwd"], options["env"]], default=str)
            self.assertNotIn(AGENT, told)
            self.assertNotIn(MODEL, told)
            self.assertNotIn(str(out), told)
            self.assertEqual(argv[2:], ["fakebench", "t1", "work", "oracle.json"])
            self.assertEqual(list(options["env"]), ["PATH"])

    def test_grading_is_outside_the_container(self):
        calls = []

        def grader(*args):
            calls.append(len(self.runtime.commands))
            return {"score": 0.0, "right": {"q1": False}, "answers": None, "answers_file": "missing or not JSON"}

        self.batch(grader=grader).run()
        self.assertEqual(len(calls), 2)
        self.assertFalse(any("grading" in " ".join(map(str, c["argv"])) for c in self.runtime.commands))


@unittest.skipUnless(BUILT, "knows2 order-sync is not built")
class Knows2(unittest.TestCase):
    def grade(self, answers):
        with tempfile.TemporaryDirectory() as scratch:
            work = Path(scratch) / "anything"
            work.mkdir()
            if answers is not None:
                (work / "answers.json").write_text(answers)
            return grading.blind("knows2", "order-sync", work, knows2.oracle("order-sync"))

    def test_the_oracles_answers_grade_one_and_no_answers_zero(self):
        oracle = knows2.oracle("order-sync").read_text()
        whole = self.grade(oracle)
        self.assertEqual(whole["score"], 1.0)
        self.assertEqual(list(whole["right"]), list(knows2.runner().rules.RULES["order-sync"]))
        self.assertEqual(self.grade(None)["score"], 0.0)
        self.assertEqual(self.grade("not json")["answers_file"], "missing or not JSON")

    def test_the_grade_is_that_of_knows2s_own_rules(self):
        oracle = json.loads(knows2.oracle("order-sync").read_text())
        half = dict(list(oracle.items())[:4])
        run = knows2.runner()
        self.assertEqual(self.grade(json.dumps(half))["score"], run.grade.grade("order-sync", half, oracle)[0])
        self.assertEqual(self.grade(json.dumps(half))["score"], 0.5)


if __name__ == "__main__":
    unittest.main()
