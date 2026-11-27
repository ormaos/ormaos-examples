"""Run the tasks of knows2: for every task, arm and run, one agent in a
fresh folder, with the runner and the report of ``../knows/run.py``.

    python3 run.py --runs 3 --replacements 0           # 9 tasks x 4 arms x 3 runs
    python3 run.py --tasks rl-env --arms ormaos --runs 1 --out results/try
    python3 run.py --report results/<name>             # write the report again
    python3 run.py --grade <task> <answers.json>       # grade one file

What is different from knows: the folders, the answers and the rules are
those of this folder; there is a fourth arm, ``ormaos-values``; the format
of an answer is the one the question writer gave; the report lists the
dropped questions and has its own limits.

Every slot is run once and counts: the first attempt, no discards.
``--replacements`` takes only 0, the number of runs that are run again.
"""

import json
import sys

import k2
import rules
from k2 import BUILD, HERE, KNOWS, TASKS, benchlib, grade, tasks

benchlib.ARMS = k2.ARMS
base = benchlib.load(KNOWS / "run.py", "knows_run")
base.BUILD, base.HERE = BUILD, HERE
knows_prompt, knows_report = tasks.prompt, base.write_report


def prompt(name, arm):
    """The task text of knows; the sentence of `ormaos-values` is the one of
    `ormaos` and says that values were recorded."""
    if arm != "ormaos-values":
        return knows_prompt(name, arm)
    return knows_prompt(name, "ormaos").replace("recorded with Ormaos:", "recorded with Ormaos, values included:")


tasks.prompt = prompt

LIMITS = [
    "The questions were written by claude-opus-5-5 from the source, the README and the printed output of each "
    "program, one writer per task, one attempt; the prompt, the transcript and the questions are in `writer/`. "
    "The programs and the executions are still those the makers of Ormaos wrote for `knows`.",
    "The agents and the question writer are the same model.",
    "The oracle (`oracle.py`, `tracer.py`) and the rule of each question (`rules.json`) were written by the "
    "makers of Ormaos after reading the questions and before any agent ran. Where a question can be read in "
    "two ways the oracle answers one of them.",
    "A question is dropped only when the oracle cannot give one unambiguous answer; a question that an arm "
    "cannot answer is kept.",
    "The writer's folder had no input file, so some questions ask for what the removed input held; the writer "
    "of `rl-env` ran the program in its folder before writing.",
    "`notebook`: the cells call `ormaos.record()` themselves. In `ormaos-values` a cell that is not of the "
    "notebook first makes that call record values; it is not `ormaos run --values`. The printed output given "
    "to the writer is that of the process that ran the kernel, not of the cells.",
    "Values in a recording are cut at 200 characters, and likely secrets are written as `***`.",
    "Four of the nine programs (`web-backend`, `ml-training`, `rl-env`, `agent-change`) read no input that can "
    "be taken away, so an agent can run them again; the report says how many runs did.",
    "One model, one prompt per arm, one tracer with its default settings, N runs per task and arm as shown.",
    "The dates in the data of the two jobs are relative to the day `build.py` ran: build on the day of the run.",
]


def write_report(out):
    text = knows_report(out).replace("# agent-bench/knows: what an agent knows about an execution",
                                     "# agent-bench/knows2: the same executions, questions by a writer who was "
                                     "not told what Ormaos records", 1)
    text = text.replace("by the rules written in `rules.json` before the run",
                        "by the rules written in `rules.json` before any agent ran")
    built = json.loads((out / "build.json").read_text())
    dropped = [f"- {name}, {qid}: \"{question(name, qid)}\" Reason: {reason}."
               for name, task in built["tasks"].items() for qid, reason in task.get("dropped", {}).items()]
    total = sum(len(json.loads((HERE / "writer" / name / "questions.json").read_text())) for name in built["tasks"])
    section = ["## Dropped questions", "",
               f"The writers wrote {total} questions; {len(dropped)} dropped, each because the oracle cannot give "
               "one unambiguous answer.", "", *(dropped or ["None."]), ""]
    head, limits = text.split("## Limits\n", 1)
    mine, rest = limits.split("\n## ", 1)
    mine = mine.rstrip("\n") + "\n" + "\n".join(f"- {line}" for line in LIMITS) + "\n"
    text = head + "\n".join(section) + "\n## Limits\n" + mine + "\n## " + rest
    (out / "report.md").write_text(text, encoding="utf-8")
    return text


def question(name, qid):
    written = json.loads((HERE / "writer" / name / "questions.json").read_text(encoding="utf-8"))
    return next(q["question"] for q in written if q["id"] == qid)


base.write_report = write_report


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--grade" in argv:
        name, path = argv[argv.index("--grade") + 1:][:2]
        oracle = json.loads((BUILD / "answers" / f"{name}.json").read_text(encoding="utf-8"))
        score, right = grade.grade(name, grade.read_answers(path), oracle)
        print("  ".join(f"{qid}:{'right' if ok else 'wrong'}" for qid, ok in right.items()))
        print(f"{name}: score {score:.3f}")
        return 0
    if "--replacements" in argv:
        at = argv.index("--replacements")
        if argv[at + 1:at + 2] != ["0"]:
            sys.exit("--replacements takes only 0: every slot is run once and counts")
        del argv[at:at + 2]
    manifest = BUILD / "manifest.json"
    if "--report" not in argv and manifest.exists():
        built = json.loads(manifest.read_text())["tasks"]
        for name in built:  # the questions that were built are the questions that are graded
            if list(rules.RULES[name]) != list(json.loads((BUILD / "answers" / f"{name}.json").read_text())):
                sys.exit(f"{name}: dropped.json is not what build.py left: run build.py")
    return base.main(argv)


if __name__ == "__main__":
    sys.exit(main())
