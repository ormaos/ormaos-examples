"""Run the tasks of knows2: for every task, arm and run, one agent in a
fresh folder, with the runner and the report of ``../knows/run.py``.

    python3 run.py --runs 3 --replacements 0           # 9 tasks x 4 arms x 3 runs
    python3 run.py --tasks rl-env --arms ormaos --runs 1 --out results/try
    python3 run.py --report results/<name>             # write the report again
    python3 run.py --grade <task> <answers.json>       # grade one file

What is different from knows: the folders, the answers and the rules are
those of this folder; there is a fourth arm, ``ormaos-values``; the format
of an answer is the one the question writer gave; the report counts the
answers that were right, null and wrong, lists the wrong ones and the
dropped questions, gives the cost, and has its own limits.

Every slot is run once and counts: the first attempt, no discards.
``--replacements`` takes only 0, the number of runs that are run again.
"""

import json
import statistics
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


# What was said of a results folder after its run, first in its limits.
AFTER_THE_RUN = {
    "20261127-165801": [
        "No expected result was written before the run.",
        "With --values, a list keeps its first 10 items; notebook q5, q7 and q8 need more and no arm answered them.",
    ],
}


def oracle_of(out, name):
    """The oracle's answers the run was graded against: the copy kept with the
    results, or those of the build."""
    kept = out / "oracle" / f"{name}.json"
    return json.loads((kept if kept.exists() else BUILD / "answers" / f"{name}.json").read_text(encoding="utf-8"))


def cell(value):
    return json.dumps(value, ensure_ascii=False).replace("|", "\\|")


def outcomes(out, records):
    """The section "Right, null, wrong", and the lines on cost under the
    first table."""
    arms = [a for a in k2.ARMS if any(r["arm"] == a for r in records)]
    count = {arm: {"right": 0, "null": 0, "wrong": 0} for arm in arms}
    wrong = []
    for r in records:
        for qid, ok in r["right"].items():
            given = r["answers"].get(qid) if isinstance(r["answers"], dict) else None
            kind = "right" if ok else "null" if given is None else "wrong"
            count[r["arm"]][kind] += 1
            if kind == "wrong":
                wrong.append((r, qid, given))
    order = {name: i for i, name in enumerate(tasks.NAMES)}
    wrong.sort(key=lambda w: (order[w[0]["task"]], arms.index(w[0]["arm"]), w[0]["run"], w[1]))
    lines = ["## Right, null, wrong", "",
             "Every answer of every run: right by the rule of its question; null, the agent wrote null; wrong, "
             "an answer that is not null and that the rule marks wrong.", "",
             "| Arm | Answers | Right | Null | Wrong |", "|---|---|---|---|---|"]
    lines += [f"| {arm} | {sum(c.values())} | {c['right']} | {c['null']} | {c['wrong']} |"
              for arm, c in count.items()]
    lines += ["", "Every wrong answer:", ""]
    if wrong:
        lines += ["| Task | Arm | Run | Question | Answer | Oracle |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['task']} | {r['arm']} | {r['run']} | {qid} | {cell(given)} | "
                  f"{cell(oracle_of(out, r['task'])[qid])} |" for r, qid, given in wrong]
    else:
        lines.append("None.")
    costs = [r["cost_usd"] for r in records if r.get("cost_usd") is not None]
    mean = {arm: [r["cost_usd"] for r in records if r["arm"] == arm and r.get("cost_usd") is not None]
            for arm in arms}
    cost = (f"Cost, as the claude command line reports it (`total_cost_usd`): ${sum(costs):.2f} for "
            f"{len(costs)} runs; mean per run, "
            + ", ".join(f"{arm} ${statistics.fmean(v):.3f}" for arm, v in mean.items() if v) + ".")
    return "\n".join(lines) + "\n", cost


def gap_lines(records):
    """The raw-to-ormaos gap task by task, and whether their intervals overlap."""
    of = lambda arm, name=None: [r["score"] for r in records  # noqa: E731
                                 if r["arm"] == arm and name in (None, r["task"])]
    if not (of("raw") and of("ormaos")):
        return []
    names = [n for n in tasks.NAMES if of("raw", n) and of("ormaos", n)]
    part = {n: (statistics.fmean(of("ormaos", n)) - statistics.fmean(of("raw", n))) / len(names) for n in names}
    gap = statistics.fmean(of("ormaos")) - statistics.fmean(of("raw"))
    shown = [f"{n} {part[n]:+.3f}" for n in names if round(part[n], 3) != 0]
    lines = [f"- The gap between raw and ormaos in the mean score is {gap:.3f}. Per task, the difference of the "
             f"task's mean scores divided by {len(names)}, every task where it is not zero: "
             + (", ".join(shown) if shown else "none") + "."]
    (raw_low, raw_high), (orm_low, orm_high) = base.bootstrap(of("raw")), base.bootstrap(of("ormaos"))
    if raw_low <= orm_high and orm_low <= raw_high:
        lines.append("- The intervals of raw and ormaos overlap.")
    return lines


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
    records = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines() if line]
    section_outcomes, cost = outcomes(out, records)
    first = "\n\n## Mean score per task\n"  # the first table and its notes end here
    text = text.replace(first, f"\n\n{cost}\n\n{section_outcomes}{first[1:]}", 1)
    head, limits = text.split("## Limits\n", 1)
    mine, rest = limits.split("\n## ", 1)
    kept = [line for line in mine.strip("\n").splitlines() if not line.startswith("- Of the gap of ")]
    said = [f"- {line}" for line in AFTER_THE_RUN.get(out.resolve().name, [])]
    mine = "\n" + "\n".join(said + kept + gap_lines(records) + [f"- {line}" for line in LIMITS]) + "\n"
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
