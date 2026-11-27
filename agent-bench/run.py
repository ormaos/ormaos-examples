"""Run the benchmark: for every bug, arm and run, one agent in a fresh folder.

    python3 run.py --runs 3                           # every bug, every arm
    python3 run.py --bugs fx-rates --arms none --runs 1 --out results/try
    python3 run.py --report results/<name>            # write the report again

A run: ``task/`` and what the arm adds are copied to a new folder, the
folder is mounted at ``/srv/<bug>`` in bubblewrap with nothing else of this
machine but the system, the claude program and its login, and ``claude -p``
is asked to find the cause and fix it. When it ends, or the time is up, the
bug's ``hidden/check.py`` judges the code it left.

The report counts the first attempt of every bug, arm and run, all of
them. An attempt in which the agent named a path outside its folder, or
that the claude command line ended with an error (no answer from the
model), is marked ``discarded`` in ``results.jsonl`` and run again; the
report lists the marked and the later attempts and does not count the later
ones. A run that used up its time counts, with what it left.

Build first: ``python3 build.py``.
"""

import argparse
import json
import os
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

import benchlib

MODEL = "claude-opus-5-5"
TOOLS = "Bash,Read,Grep,Glob,Edit,Write"
# Places of the sandbox that are not the agent's folder and not the system's
# programs and libraries. /tmp is the sandbox's own and starts empty.
OUTSIDE = ("/home", "/root", "/etc", "/var", "/opt", "/srv", "/mnt", "/media", "/run", "/boot")
INSIDE = ("/tmp", "/dev", "/usr", "/bin", "/lib", "/lib64", "/sbin", "/proc", "/sys")
LOCAL_URL = re.compile(r"\w+://(127\.0\.0\.1|localhost|\[::1\]|\{|\$|%)")
PATH_IN_COMMAND = re.compile(r"""(?<![\w.\-/:])(/[\w.\-/]*)""")


def is_under(path, root):
    return path == root or path.startswith(root + "/")


def outside_paths(tool, given, mount):
    """The paths outside the folder that one tool call names. (sure, to look at)."""
    sure, look = [], []
    if tool == "Bash":
        command = str(given.get("command", ""))
        # The network is open for the model only: another host is outside too.
        sure += [url for url in re.findall(r"\w+://[^\s\"')]+", command) if not LOCAL_URL.match(url)]
        command = re.sub(r"\w+://\S+", " ", command)
        for path in PATH_IN_COMMAND.findall(command):
            path = os.path.normpath(path)
            if is_under(path, mount):
                continue
            if is_under(path, benchlib.VIZTRACER):
                continue  # a name in the trace; the sandbox has no such folder
            if path == "/" or any(is_under(path, root) for root in OUTSIDE):
                sure.append(path)
        if re.search(r"(^|[\s\"'=(])(~|\$HOME|\$\{HOME\})(/|[\s\"')]|$)", command):
            sure.append("~")
        look += re.findall(r"(?:^|[\s\"'=(])((?:\.\./)+[\w.\-/]*|\.\.)(?=[\s\"');|&]|$)", command)
    else:
        for key in ("file_path", "path", "notebook_path"):
            path = given.get(key)
            if not path:
                continue
            path = os.path.normpath(path if os.path.isabs(path) else f"{mount}/{path}")
            if not is_under(path, mount) and not any(is_under(path, root) for root in INSIDE):
                sure.append(path)
    return sure, look


def read_stream(path, mount):
    """What the agent did, from the stream ``claude -p`` wrote."""
    facts = {"tool_calls": 0, "tools": {}, "outside": [], "to_look_at": [],
             "mcp_servers": None, "result": None}
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "system" and event.get("subtype") == "init":
                facts["mcp_servers"] = event.get("mcp_servers")
                facts["model"] = event.get("model")
                facts["claude"] = event.get("claude_code_version")
            elif event.get("type") == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") != "tool_use":
                        continue
                    tool = block.get("name", "?")
                    facts["tool_calls"] += 1
                    facts["tools"][tool] = facts["tools"].get(tool, 0) + 1
                    sure, look = outside_paths(tool, block.get("input") or {}, mount)
                    facts["outside"] += sure
                    facts["to_look_at"] += look
            elif event.get("type") == "result":
                facts["result"] = event
    return facts


def one_attempt(name, arm, run, attempt, out, args):
    slot = f"{name}-{arm}-{run}" + (f"-again{attempt}" if attempt else "")
    folder = out / "work" / slot
    stream = out / "streams" / f"{slot}.jsonl"
    mount = benchlib.mount_of(name)
    benchlib.assemble(name, arm, folder)
    command = [
        *benchlib.sandbox(folder, mount, network=True, claude=True),
        args.claude, "-p", "--model", args.model, "--safe-mode", "--strict-mcp-config",
        "--tools", TOOLS, "--allowedTools", TOOLS, "--no-session-persistence",
        "--output-format", "stream-json", "--verbose", benchlib.prompt(name, arm),
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

    facts = read_stream(stream, mount)
    result = facts["result"] or {}
    usage = result.get("usage") or {}
    check = subprocess.run(
        [sys.executable, str(benchlib.BUGS / name / "hidden" / "check.py"), str(folder)],
        capture_output=True, text=True, check=False, timeout=600,
    )
    shutil.rmtree(folder / ".venv", ignore_errors=True)

    why = None
    if facts["outside"]:
        why = "named a path outside its folder: " + ", ".join(sorted(set(facts["outside"])))
    elif facts["mcp_servers"]:
        why = f"MCP servers were connected: {facts['mcp_servers']}"
    elif not timed_out and (facts["result"] is None or result.get("is_error")):
        said = f"{result.get('subtype', 'no result')}: {result.get('result') or ''}"
        why = "the agent ended with an error of the command line or the model: " + said[:200]
    return {
        "bug": name, "arm": arm, "run": run, "attempt": attempt,
        "fixed": check.returncode == 0,
        "check": check.stdout.strip().splitlines() or check.stderr.strip().splitlines()[-3:],
        "wall_seconds": wall,
        "timed_out": timed_out,
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
        "read_outside": sorted(set(facts["outside"])),
        "to_look_at": sorted(set(facts["to_look_at"])),
        "discarded": why,
        "model": facts.get("model") or args.model,
        "claude": facts.get("claude"),
        "started": started,
        "stream": str(stream.relative_to(out)),
        "folder": str(folder.relative_to(out)),
    }


def one_run(name, arm, run, out, args, write):
    """A run that counts, or ``args.replacements`` discarded attempts."""
    for attempt in range(args.replacements + 1):
        record = one_attempt(name, arm, run, attempt, out, args)
        write(record)
        if record["discarded"] is None:
            return


def tokens_of(record):
    tokens = record.get("tokens") or {}
    values = [v for v in tokens.values() if v is not None]
    return sum(values) if values else None


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def cell(fixed, total):
    if not total:
        return "no run"
    low, high = benchlib.wilson(fixed, total)
    return f"{fixed}/{total} ({100 * low:.0f}%-{100 * high:.0f}%)"


ENDED = re.compile(r"^(?:FAIL\s+(?P<case>.+?): )?[\w-]+: the job did not finish with '(?P<line>[^']+)':$")


def reason(record):
    """What the check said against the code: its lines other than the passes."""
    said = [line for line in record["check"] if not line.startswith("pass ") and line != "not fixed"]
    parts = []
    for index, line in enumerate(said):
        ended = ENDED.match(line)
        if not ended:
            if not (index and ENDED.match(said[index - 1])):
                parts.append(line.strip())
            continue
        part = f"the job did not end with `{ended['line']}`"
        if ended["case"]:
            part = f"{ended['case']}: {part}"
        following = said[index + 1] if index + 1 < len(said) else None
        if following and not following.startswith("FAIL") and not ENDED.match(following):
            part += f"; it printed `{following.strip()}`"
        parts.append(part)
    return "; ".join(parts) or "the check gave no reason"


def ended_otherwise(record):
    return any(ENDED.match(line) for line in record["check"])


# Not-fixed first attempts whose folders were read by hand after the run, per
# results folder: each fixed the cause and changed only the job's last line.
READ_AFTER_THE_RUN = {
    "20261126-220703": {("late-fees", "raw", 1), ("fx-rates", "none", 2),
                        ("fx-rates", "none", 3), ("late-fees", "none", 3)},
}


def overlap(intervals):
    return max(low for low, _ in intervals) <= min(high for _, high in intervals)


def write_report(out):
    records = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines() if line]
    # What counts is the first attempt of every bug, arm and run, as planned
    # before the run. Later attempts were made after an attempt was marked
    # (see the README) and are listed only.
    first = [r for r in records if r["attempt"] == 0]
    marked = [r for r in records if r["discarded"] is not None]
    later = [r for r in records if r["attempt"] > 0]
    arms = [a for a in benchlib.ARMS if any(r["arm"] == a for r in records)]
    bugs = sorted({r["bug"] for r in records})
    manifest = benchlib.TOOLS / "manifest.json"
    built = json.loads(manifest.read_text()) if manifest.exists() else {}
    if (out / "build.json").exists():
        built = json.loads((out / "build.json").read_text())

    def of(arm, bug=None):
        return [r for r in first if r["arm"] == arm and bug in (None, r["bug"])]

    lines = ["# agent-bench: fixes per arm", ""]
    lines.append(
        f"N = {len(first)} runs, the first attempt of every bug, arm and run; all of them count. "
        f"{len(bugs)} bugs x {len(arms)} arms x {len({r['run'] for r in first})} runs. "
        f"Model: {', '.join(sorted({str(r['model']) for r in records})) or MODEL}. "
        f"Ormaos {built.get('ormaos_commit', '?')}, VizTracer {built.get('viztracer', '?')}, "
        f"{built.get('python', '?')}; built {built.get('built', '?')}."
    )
    lines += ["", "Fixed means that the bug's `hidden/check.py` passed on the code the agent left. "
              "The interval is the 95% Wilson score interval.", ""]
    lines += ["| Arm | Fixed | 95% interval | Median wall time | Median tool calls | Median tokens | Timed out |",
              "|---|---|---|---|---|---|---|"]
    intervals = []
    for arm in arms:
        runs = of(arm)
        fixed = sum(r["fixed"] for r in runs)
        low, high = benchlib.wilson(fixed, len(runs))
        intervals.append((low, high))
        wall, calls = median(r["wall_seconds"] for r in runs), median(r["tool_calls"] for r in runs)
        tokens = median(tokens_of(r) for r in runs)
        lines.append(
            f"| {arm} | {fixed}/{len(runs)} | {100 * low:.0f}% to {100 * high:.0f}% | "
            f"{'-' if wall is None else f'{wall:.0f} s'} | {'-' if calls is None else f'{calls:g}'} | "
            f"{'-' if tokens is None else f'{tokens:,.0f}'} | {sum(r['timed_out'] for r in runs)} |"
        )
    lines += ["", "Tokens are input, output and cache tokens added up, as the claude command line reports them.", ""]
    if overlap(intervals):
        lines.append("At this size the difference is within the margin: the 95% intervals of the arms "
                     "overlap, so these runs do not show that one arm fixes more bugs than another.")
    else:
        lines.append("The 95% intervals of the arms do not all overlap.")
    lines += ["", "## Per bug", "", "| Bug | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for bug in bugs:
        cells = [cell(sum(r["fixed"] for r in of(arm, bug)), len(of(arm, bug))) for arm in arms]
        lines.append(f"| {bug} | " + " | ".join(cells) + " |")

    not_fixed = [r for r in first if not r["fixed"]]
    lines += ["", "## Not fixed", "", "The first attempts that the check did not pass, with what the check said.", ""]
    lines += [f"- {r['bug']}, {r['arm']}, run {r['run']}: {reason(r)} (`{r['stream']}`, `{r['folder']}`)"
              for r in not_fixed] or ["None."]
    if not_fixed and all(ended_otherwise(r) for r in not_fixed):
        lines += ["", "In each of them, on a night that the check expects to end OK, the job the agent left "
                  "did not end with exit code 0 and its OK line exactly as before. The check reads the end "
                  "of a night as cron does, so it rejects a changed last line."]

    read = READ_AFTER_THE_RUN.get(out.resolve().name)
    if read and {(r["bug"], r["arm"], r["run"]) for r in not_fixed} == read and all(map(ended_otherwise, not_fixed)):
        counts = ", ".join(f"{arm} {len(of(arm))}/{len(of(arm))}" for arm in arms)
        lines += ["", "## After the run", "",
                  "This is an analysis made after seeing the results; it was not planned before the run "
                  "and changes nothing in the tables above.", "",
                  f"In all {len(not_fixed)} first attempts that were not fixed, the agent found the cause and "
                  "fixed it (read by hand in the folders it left), but also changed the job's last line, which "
                  f"the check rejects. Counted as fixed, every arm would be {len(of(arms[0]))}/{len(of(arms[0]))} "
                  f"({counts}), so this benchmark does not separate the arms."]

    lines += ["", "## Marked attempts", "",
              "Attempts in which the agent named a path outside its folder. The sandbox has nothing there "
              "to find: `/etc` is the host's, read-only, and holds nothing of these jobs; the home folder, "
              "`/var` and `/tmp` are empty; `/opt` does not exist and `/srv` holds only the agent's folder. "
              "The first attempts among them count in the tables above; each was run again, "
              f"and the {len(later)} later attempts are listed here and do not count.", ""]
    if marked:
        lines += ["| Bug | Arm | Run | Attempt | Fixed | Paths named | Stream |", "|---|---|---|---|---|---|---|"]
        lines += [f"| {r['bug']} | {r['arm']} | {r['run']} | {r['attempt']} | {'yes' if r['fixed'] else 'no'} | "
                  f"{', '.join(r['read_outside']) or r['discarded']} | `{r['stream']}` |" for r in marked]
    else:
        lines.append("None.")
    unmarked_later = [r for r in later if r["discarded"] is None]
    if unmarked_later:
        lines += ["", "Later attempts that were not marked (they do not count either):", ""]
        lines += [f"- {r['bug']}, {r['arm']}, run {r['run']}, attempt {r['attempt']}: "
                  f"{'fixed' if r['fixed'] else 'not fixed'} (`{r['stream']}`)" for r in unmarked_later]

    looked = [r for r in first if r["to_look_at"]]
    lines += ["", "## Runs that used `..` in a command", "",
              "`..` from a subfolder stays inside the folder. To look at by hand.", ""]
    lines += [f"- {r['bug']}, {r['arm']}, run {r['run']}: {', '.join(r['to_look_at'])} (`{r['stream']}`)"
              for r in looked] or ["None."]
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text, encoding="utf-8")
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bugs", default=",".join(benchlib.bug_names()))
    parser.add_argument("--arms", default=",".join(benchlib.ARMS))
    parser.add_argument("--runs", type=int, default=1, help="runs per bug and arm")
    parser.add_argument("--timeout", type=int, default=900, help="seconds for one agent")
    parser.add_argument("--jobs", type=int, default=3, help="agents at the same time")
    parser.add_argument("--replacements", type=int, default=3,
                        help="how often a discarded run is run again")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--out", type=Path, default=None, help="default: results/<now>")
    parser.add_argument("--report", type=Path, metavar="DIR", help="only write the report again")
    args = parser.parse_args(argv)
    if args.report:
        print(write_report(args.report))
        return 0

    bugs, arms = args.bugs.split(","), args.arms.split(",")
    for name in bugs:
        for part in ("task/TASK.md", "arms/raw/result.json", "arms/ormaos/.ormaos"):
            if not (benchlib.BUGS / name / part).exists():
                parser.error(f"{name} is not built: run build.py")
    args.claude = os.path.realpath(shutil.which("claude") or parser.error("claude is not installed"))
    out = (args.out or benchlib.ROOT / "results" / datetime.now().strftime("%Y%m%d-%H%M%S")).resolve()
    if (out / "results.jsonl").exists():
        parser.error(f"{out} already has results")
    (out / "work").mkdir(parents=True)
    (out / "streams").mkdir()
    shutil.copy(benchlib.TOOLS / "manifest.json", out / "build.json")
    results = open(out / "results.jsonl", "a", encoding="utf-8")

    def write(record):
        results.write(json.dumps(record) + "\n")
        results.flush()
        state = "discarded" if record["discarded"] else ("fixed" if record["fixed"] else "not fixed")
        print(f"{record['bug']:17} {record['arm']:7} run {record['run']}: {state}, "
              f"{record['wall_seconds']:.0f} s, {record['tool_calls']} tool calls", flush=True)

    # Run by run, so that the arms of a bug are spread over the time the whole takes.
    slots = [(name, arm, run) for run in range(1, args.runs + 1) for name in bugs for arm in arms]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        waiting = [pool.submit(one_run, name, arm, run, out, args, write) for name, arm, run in slots]
        for future in waiting:
            future.result()
    results.close()
    print()
    print(write_report(out))
    print(f"results: {out / 'results.jsonl'}\nreport:  {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
