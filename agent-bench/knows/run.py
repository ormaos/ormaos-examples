"""Run the tasks: for every task, arm and run, one agent in a fresh folder.

    python3 run.py --runs 3                            # 9 tasks x 3 arms x 3 runs
    python3 run.py --tasks rl-env --arms none --runs 1 --out results/try
    python3 run.py --report results/<name>             # write the report again

A run: the folder of the task and arm is copied to a new folder, mounted at
``/srv/<task>`` in bubblewrap with nothing else of this machine but the
system, the claude program and its login, and ``claude -p`` gets the task
text. When it ends, or the time is up, ``answers.json`` in the folder is
graded against the oracle's answers by the rules of ``rules.json``.

Every slot is run once and counts: nothing is run again and nothing is left
out. A run that used up its time, or that the command line ended with an
error, counts with the answers it left (none: score 0). The paths outside
its folder that an agent named are recorded, as information only.

Build first: ``python3 build.py``.
"""

import argparse
import json
import os
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import grade
import tasks
from tasks import BENCH, HERE, TASKS, benchlib

bench_run = benchlib.load(BENCH / "run.py", "bench_run")  # reading a stream, as agent-bench does

BUILD = HERE / ".build"
MODEL = "claude-opus-5-5"
TOOLS = "Bash,Read,Grep,Glob,Edit,Write"
RESAMPLES = 10000


def ran_again(name, stream):
    """Whether the agent ran the program again: "script" when a command ran
    one of its scripts with Python, "import" when Python code of the agent
    (in a command or in a file it wrote) imported one of its modules."""
    task = TASKS[name]
    # Python (or a tool that runs Python) as the command itself, not as a word
    # given to grep or cat: at the start, after ; & | ( or --, after VAR=value,
    # or after timeout, time or env.
    script = re.compile(
        r"(?:^|[;&|(\n]|--)\s*(?:(?:\w+=\S*|timeout\s+\S+|time|env|exec)\s+)*(?:\S*/)?"
        r"(?:python[\d.]*|viztracer|jupyter|papermill)\s[^|;&\n]*?(?:[\s/=\"'])?(?:"
        + "|".join(map(re.escape, task["scripts"])) + r")(?![\w.])")
    module = re.compile(r"^\s*(?:import|from)\s+(?:" + "|".join(map(re.escape, task["modules"])) + r")\b", re.M)
    found = None
    with open(stream, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict) or event.get("type") != "assistant":
                continue
            for block in event.get("message", {}).get("content", []):
                if block.get("type") != "tool_use":
                    continue
                given = block.get("input") or {}
                if block.get("name") == "Bash":
                    command = str(given.get("command", ""))
                    if script.search(command):
                        return "script"
                    if "python" in command and module.search(command.replace(";", "\n").replace('"', "\n")):
                        found = "import"
                elif block.get("name") in ("Write", "Edit"):
                    text = str(given.get("content", "")) + str(given.get("new_string", ""))
                    if str(given.get("file_path", "")).endswith(".py") and module.search(text):
                        found = "import"
    return found


def one_run(name, arm, run, out, args, built):
    slot = f"{name}-{arm}-{run}"
    folder = out / "work" / slot
    stream = out / "streams" / f"{slot}.jsonl"
    mount = benchlib.mount_of(name)
    shutil.copytree(BUILD / "folders" / name / arm, folder, symlinks=True)
    command = benchlib.sandbox(folder, mount, network=True, claude=True)
    venv = built["tasks"][name]["venvs"][arm]
    if venv:
        command += ["--ro-bind", venv, f"{mount}/.venv"]
    command += [
        args.claude, "-p", "--model", args.model, "--safe-mode", "--strict-mcp-config",
        "--tools", TOOLS, "--allowedTools", TOOLS, "--no-session-persistence",
        "--output-format", "stream-json", "--verbose", tasks.prompt(name, arm),
    ]
    started = datetime.now().isoformat(timespec="seconds")
    clock = time.monotonic()
    timed_out = False
    with open(stream, "w", encoding="utf-8") as output:
        agent = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            agent.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(agent.pid, signal.SIGKILL)
            agent.wait()
    wall = round(time.monotonic() - clock, 1)

    facts = bench_run.read_stream(stream, mount)
    result = facts["result"] or {}
    usage = result.get("usage") or {}
    answers = grade.read_answers(folder / "answers.json")
    oracle = json.loads((BUILD / "answers" / f"{name}.json").read_text(encoding="utf-8"))
    score, right = grade.grade(name, answers, oracle)
    error = None
    if facts["mcp_servers"]:
        error = f"MCP servers were connected: {facts['mcp_servers']}"
    elif not timed_out and (facts["result"] is None or result.get("is_error")):
        error = f"{result.get('subtype', 'no result')}: {result.get('result') or ''}"[:200]
    again = ran_again(name, stream)
    # The trace is the same file in every run of the arm: keep one copy, in .build.
    for trace in folder.glob("result*.json"):
        trace.unlink()
    return {
        "task": name, "arm": arm, "run": run,
        "score": score,
        "right": right,
        "answers": answers,
        "answers_file": "missing or not JSON" if answers is None else "read",
        "wall_seconds": wall,
        "timed_out": timed_out,
        "error": error,
        "tool_calls": facts["tool_calls"],
        "tools": facts["tools"],
        "turns": result.get("num_turns"),
        "tokens": {
            "input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
            "cache_read": usage.get("cache_read_input_tokens"),
            "cache_write": usage.get("cache_creation_input_tokens"),
        } if usage else None,
        "cost_usd": result.get("total_cost_usd"),
        "ran_again": again,
        "named_outside": sorted(set(facts["outside"])),
        "model": facts.get("model") or args.model,
        "claude": facts.get("claude"),
        "started": started,
        "stream": str(stream.relative_to(out)),
        "folder": str(folder.relative_to(out)),
    }


def bootstrap(scores, seed=20261127):
    """The 95% interval of the mean: percentiles of the means of RESAMPLES
    resamples of the runs, drawn with replacement."""
    if not scores:
        return (0.0, 1.0)
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(scores, k=len(scores))) for _ in range(RESAMPLES))
    return means[int(0.025 * RESAMPLES)], means[int(0.975 * RESAMPLES) - 1]


def number(value, form="{:,.0f}"):
    return "-" if value is None else form.format(value)


# What was said of a results folder after its run: whether an expectation was
# written before it, and why the task with the largest gap between raw and
# ormaos has it.
AFTER_THE_RUN = {
    "20261127-140018": {
        "before": "No expectation was written before this run: the rules of `rules.json` were, what each "
                  "arm would score was not.",
        "why": {"data-pipeline": "its questions ask the row counts of DataFrames, which Ormaos records "
                                 "and VizTracer with its default settings does not"},
    },
}


def write_report(out):
    records = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines() if line]
    built = json.loads((out / "build.json").read_text())
    arms = [a for a in benchlib.ARMS if any(r["arm"] == a for r in records)]
    names = [n for n in tasks.NAMES if any(r["task"] == n for r in records)]
    runs = len({r["run"] for r in records})
    median, tokens_of = bench_run.median, bench_run.tokens_of

    def of(arm, name=None):
        return [r for r in records if r["arm"] == arm and name in (None, r["task"])]

    lines = ["# agent-bench/knows: what an agent knows about an execution", ""]
    lines.append(
        f"N = {len(records)} runs: {len(names)} tasks x {len(arms)} arms x {runs} runs, every slot run once, "
        f"all of them counted. Model: {', '.join(sorted({str(r['model']) for r in records})) or MODEL}. "
        f"Ormaos {built.get('ormaos_commit', '?')}, VizTracer {built.get('viztracer', '?')}, "
        f"{built.get('python', '?')}; built {built.get('built', '?')}."
    )
    lines += ["", "The score of a run is the share of the task's questions that its `answers.json` got right, "
              "by the rules written in `rules.json` before the run. The interval is a 95% bootstrap interval "
              f"of the mean over the runs of the arm ({RESAMPLES:,} resamples).", ""]
    lines += ["| Arm | Runs | Mean score | 95% interval | Median wall time | Median tool calls | Median tokens "
              "| Ran the program again | Timed out |", "|---|---|---|---|---|---|---|---|---|"]
    for arm in arms:
        mine = of(arm)
        scores = [r["score"] for r in mine]
        low, high = bootstrap(scores)
        lines.append(
            f"| {arm} | {len(mine)} | {statistics.fmean(scores):.2f} | {low:.2f} to {high:.2f} | "
            f"{number(median(r['wall_seconds'] for r in mine))} s | "
            f"{number(median(r['tool_calls'] for r in mine), '{:g}')} | "
            f"{number(median(tokens_of(r) for r in mine))} | "
            f"{sum(bool(r['ran_again']) for r in mine)}/{len(mine)} | {sum(r['timed_out'] for r in mine)} |")
    lines += ["", "Tokens are input, output and cache tokens added up, as the claude command line reports them. "
              "An agent ran the program again when a command of its ran one of the program's scripts, or its "
              "own Python code imported one of the program's modules."]

    for title, cell in (
        ("Mean score per task", lambda mine: number(statistics.fmean(r["score"] for r in mine), "{:.2f}")),
        ("Median wall time per task, in seconds", lambda mine: number(median(r["wall_seconds"] for r in mine))),
        ("Median tokens per task", lambda mine: number(median(tokens_of(r) for r in mine))),
        ("Runs that ran the program again, per task",
         lambda mine: f"{sum(bool(r['ran_again']) for r in mine)}/{len(mine)}"),
    ):
        lines += ["", f"## {title}", "", "| Task | Questions | " + " | ".join(arms) + " |",
                  "|---|---|" + "---|" * len(arms)]
        for name in names:
            cells = [cell(of(arm, name)) if of(arm, name) else "no run" for arm in arms]
            lines.append(f"| {name} | {len(grade.RULES[name])} | " + " | ".join(cells) + " |")

    lines += ["", "## Per question", "", "Runs that got the question right, out of the runs of the arm.", "",
              "| Task | Question | " + " | ".join(arms) + " |", "|---|---|" + "---|" * len(arms)]
    for name in names:
        for qid in grade.RULES[name]:
            cells = [f"{sum(r['right'][qid] for r in of(arm, name))}/{len(of(arm, name))}" for arm in arms]
            lines.append(f"| {name} | {qid} | " + " | ".join(cells) + " |")

    said = AFTER_THE_RUN.get(out.resolve().name, {})
    perfect = [n for n in names if all(statistics.fmean(r["score"] for r in of(a, n)) == 1 for a in arms if of(a, n))]
    lines += ["", "## Limits", ""]
    lines += [f"- {said['before']}"] if "before" in said else []
    lines.append(f"- In {len(perfect)} of {len(names)} tasks every arm scored 1.00 ({', '.join(perfect)}); "
                 "those tasks do not separate the arms.")
    if {"raw", "ormaos"} <= set(arms) and len(of("raw")) == len(of("ormaos")):
        part = {n: (sum(r["score"] for r in of("ormaos", n)) - sum(r["score"] for r in of("raw", n)))
                / len(of("raw")) for n in names}
        gap = sum(part.values())
        top = max(part, key=part.get)
        if gap > 0 and part[top] > 0:
            why = said.get("why", {}).get(top)
            lines.append(f"- Of the gap of {gap:.2f} between raw and ormaos in the mean score, {part[top]:.2f} "
                         f"comes from {top}" + (f": {why}." if why else "."))

    ended = [r for r in records if r["timed_out"] or r["error"] or r["answers_file"] != "read"]
    lines += ["", "## Runs that ended otherwise", "",
              "Out of time, an error of the command line or the model, or no `answers.json` that reads as JSON. "
              "They count, with the score shown.", ""]
    lines += [f"- {r['task']}, {r['arm']}, run {r['run']}: score {r['score']:.2f}; "
              + "; ".join(filter(None, ["out of time" if r["timed_out"] else None, r["error"],
                                        None if r["answers_file"] == "read" else "answers.json " + r["answers_file"]]))
              + f" (`{r['stream']}`)" for r in ended] or ["None."]
    outside = [r for r in records if r["named_outside"]]
    lines += ["", "## Paths outside the folder", "",
              "Runs in which the agent named a path outside its folder, or another host. Information only: "
              "these runs count like the others. The sandbox has nothing of the tasks outside the folder.", ""]
    lines += [f"- {r['task']}, {r['arm']}, run {r['run']}: {', '.join(r['named_outside'])} (`{r['stream']}`)"
              for r in outside] or ["None."]
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text, encoding="utf-8")
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tasks", default=",".join(tasks.NAMES))
    parser.add_argument("--arms", default=",".join(benchlib.ARMS))
    parser.add_argument("--runs", type=int, default=1, help="runs per task and arm")
    parser.add_argument("--timeout", type=int, default=900, help="seconds for one agent")
    parser.add_argument("--jobs", type=int, default=3, help="agents at the same time")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--out", type=Path, default=None, help="default: results/<now>")
    parser.add_argument("--report", type=Path, metavar="DIR", help="only write the report again")
    args = parser.parse_args(argv)
    if args.report:
        print(write_report(args.report.resolve()))
        return 0

    names, arms = args.tasks.split(","), args.arms.split(",")
    manifest = BUILD / "manifest.json"
    built = json.loads(manifest.read_text()) if manifest.exists() else {"tasks": {}}
    for name in names:
        if name not in built["tasks"] or not (BUILD / "answers" / f"{name}.json").exists():
            parser.error(f"{name} is not built: run build.py")
    args.claude = os.path.realpath(shutil.which("claude") or parser.error("claude is not installed"))
    out = (args.out or HERE / "results" / datetime.now().strftime("%Y%m%d-%H%M%S")).resolve()
    if (out / "results.jsonl").exists():
        parser.error(f"{out} already has results")
    (out / "work").mkdir(parents=True)
    (out / "streams").mkdir()
    shutil.copy(manifest, out / "build.json")
    results = open(out / "results.jsonl", "a", encoding="utf-8")

    def slot(name, arm, run):
        record = one_run(name, arm, run, out, args, built)
        results.write(json.dumps(record) + "\n")
        results.flush()
        print(f"{name:14} {arm:7} run {run}: score {record['score']:.2f}, {record['wall_seconds']:.0f} s, "
              f"{record['tool_calls']} tool calls" + (", ran it again" if record["ran_again"] else ""), flush=True)

    # Run by run, so that the arms of a task are spread over the time the whole takes.
    slots = [(name, arm, run) for run in range(1, args.runs + 1) for name in names for arm in arms]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for future in [pool.submit(slot, *each) for each in slots]:
            future.result()
    results.close()
    print()
    print(write_report(out))
    print(f"results: {out / 'results.jsonl'}\nreport:  {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
