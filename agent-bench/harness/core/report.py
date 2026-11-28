"""The report of a results folder.

It reads ``run.json``, ``results.jsonl`` and the event streams, and nothing
that an agent's command line printed in its own format. It fails when the
expectations of the run changed after the run started.
"""

import json
import random
import statistics
from pathlib import Path

from core import events, spec as specs

RESAMPLES = 10000


def bootstrap(scores, seed=20261127):
    """The 95% bootstrap interval of a mean."""
    if len(scores) < 2:
        return None
    pick = random.Random(seed)
    means = sorted(statistics.fmean(pick.choices(scores, k=len(scores))) for _ in range(RESAMPLES))
    return means[int(0.025 * RESAMPLES)], means[int(0.975 * RESAMPLES) - 1]


def median(values, form="{:,.0f}"):
    values = [v for v in values if v is not None]
    return form.format(statistics.median(values)) if values else "-"


def total(tokens):
    values = [v for v in (tokens or {}).values() if v is not None]
    return sum(values) if values else None


def write(out, root=specs.HARNESS):
    text = render(out, root)
    (Path(out) / "report.md").write_text(text, encoding="utf-8")
    return text


def check(out, root=specs.HARNESS):
    """Fail unless the folder still builds and its report.md is what its
    files say. Writes nothing."""
    path = Path(out) / "report.md"
    if not path.exists() or path.read_text(encoding="utf-8") != render(out, root):
        raise specs.Refused(f"{out}: report.md is not what the results and the events say")


def render(out, root=specs.HARNESS):
    out = Path(out)
    run = specs.verify(out, root)
    spec, agent, images = run["spec"], run["agent"], run["images"]
    records = [json.loads(line) for line in (out / "results.jsonl").read_text(encoding="utf-8").splitlines() if line]
    for record in records:  # the numbers of a result are those of its events
        stream = events.read(out / record["events"])
        wrong = events.stream_problems(stream)
        if wrong:
            raise specs.Refused(f"{out / record['events']}: {wrong[0]}")
        for key, value in events.summary(stream, agent["tools"]).items():
            if key != "violations" and record[key] != value:
                raise specs.Refused(f"{record['events']}: {key} of the result is not that of the events")
    arms = [arm for arm in spec["arms"] if any(r["arm"] == arm for r in records)]
    lines = [f"# agent-bench/harness: {spec['benchmark']}, {agent['name']}, {spec['model']}", ""]
    if (out / "TEST.md").exists():
        lines += ["**A test of the harness, not a result.** Nothing may be concluded from its scores.", ""]
    lines += [
        f"Spec `{spec['name']}`: {len(run['plan'])} runs planned, {len(records)} run; the first attempt of every "
        f"task, arm and run, all of them. Agent {agent['name']} {agent['cli_version']}, model {spec['model']}, "
        f"effort {spec['effort']}, {spec['n']} per task and arm, {spec['time_limit_seconds']} s per run, "
        f"{run['jobs']} at a time. Started {run['started']}, finished {run['finished'] or 'not finished'}."
        + "".join(f" Stopped {stop['at']} before {', '.join(map(str, stop['before']))}: the credential was about "
                  "to expire." for stop in run.get("stops", []))
        + "".join(f" Continued {when}, with the runs that had not started." for when in run.get("continued", [])), "",
        f"- Expectations: `{run['expectations']['file']}`, sha256 `{run['expectations']['sha256']}` when the "
        "run started; it has not changed since.",
        f"- Base image `{images['base']['id']}`, agent image `{images['agent']['id']}`, Python {images['python']}, "
        f"{run['runtime']}.",
        f"- Hosts the proxy allowed: {', '.join(agent['hosts'])}. Tools: {', '.join(agent['tools'])}. "
        f"Home folder at the start of a run: {', '.join(agent['home'])}.",
        "- Canary before the first run: " + ("all passed." if all(l.startswith("PASS ") for l in run["canary"])
                                             else "NOT all passed.") + " (`canary.txt`)", "",
    ]
    lines += ["## Per arm", "",
              "| Arm | Runs | Mean score | 95% interval | Right | Null | Wrong | Median wall time | "
              "Median tool calls | Median tokens | Cost |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm in arms:
        mine = [r for r in records if r["arm"] == arm]
        count = {"right": 0, "null": 0, "wrong": 0}
        for r in mine:
            for qid, ok in r["right"].items():
                given = r["answers"].get(qid) if isinstance(r["answers"], dict) else None
                count["right" if ok else "null" if given is None else "wrong"] += 1
        interval = bootstrap([r["score"] for r in mine])
        costs = [r["cost_usd"] for r in mine if r["cost_usd"] is not None]
        lines.append(
            f"| {arm} | {len(mine)} | {statistics.fmean(r['score'] for r in mine):.2f} | "
            f"{'-' if interval is None else f'{interval[0]:.2f} to {interval[1]:.2f}'} | "
            f"{count['right']} | {count['null']} | {count['wrong']} | "
            f"{median([r['wall_seconds'] for r in mine])} s | {median([r['tool_calls'] for r in mine], '{:g}')} | "
            f"{median([total(r['tokens']) for r in mine])} | {f'${sum(costs):.2f}' if costs else '-'} |")
    lines += ["", "Tokens are input, output and cache tokens added up, and the cost is in US dollars, both as "
              "the agent's command line reports them; different vendors count tokens differently. With one run "
              "per arm there is no interval.", ""]
    names = [name for name in dict.fromkeys(slot[0] for slot in run["plan"]) if any(r["task"] == name for r in records)]
    lines += ["## Per task", "", "Mean score of the runs of each task and arm.", "",
              "| Task | Questions | " + " | ".join(arms) + " |", "|---|---|" + "---|" * len(arms)]
    for name in names:
        mine = [r for r in records if r["task"] == name]
        means = [[r["score"] for r in mine if r["arm"] == arm] for arm in arms]
        lines.append(f"| {name} | {len(mine[0]['right'])} | "
                     + " | ".join(f"{statistics.fmean(m):.2f}" if m else "-" for m in means) + " |")
    lines += ["", "## Every run", "", "| Task | Arm | Run | Score | Wall time | Tool calls | Tokens | Cost | Ended |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        tokens = total(r["tokens"])
        lines.append(f"| {r['task']} | {r['arm']} | {r['run']} | {r['score']:.2f} | {r['wall_seconds']:.0f} s | "
                     f"{r['tool_calls']} | {'-' if tokens is None else f'{tokens:,}'} | "
                     f"{'-' if r['cost_usd'] is None else '$%.2f' % r['cost_usd']} | {r['final']} |")
    missing = [slot for slot in run["plan"] if tuple(slot) not in {(r["task"], r["arm"], r["run"]) for r in records}]
    lines += ["", "## Not as planned", ""]
    for name, arm, n in missing:
        if (out / "work" / f"{name}-{arm}-{n}").exists() or (out / "events" / f"{name}-{arm}-{n}.jsonl").exists():
            lines.append(f"- {name}, {arm}, run {n}: started, and left no result")
        else:
            lines.append(f"- {name}, {arm}, run {n}: not started (the batch stopped before it; it is not a "
                         "failure and it is not dropped)")
    lines += [f"- {r['task']}, {r['arm']}, run {r['run']}: {problem}" for r in records for problem in r["violations"]]
    lines += [f"- {r['task']}, {r['arm']}, run {r['run']}: {r['error']}" for r in records if r["error"]]
    if lines[-1] == "":
        lines.append("Nothing: every planned run has a result, with the tools and the network of the plan.")
    denied = {}
    proxy = out / "proxy.jsonl"
    for line in proxy.read_text(encoding="utf-8").splitlines() if proxy.exists() else []:
        entry = json.loads(line)
        if entry.get("allowed") is False:
            denied[entry["target"]] = denied.get(entry["target"], 0) + 1
    lines += ["", "## Refused by the proxy", "",
              "Every target the proxy refused during the batch, the canary's included, with how often.", ""]
    lines += [f"- `{target}`: {times}" for target, times in sorted(denied.items())] or ["None."]
    lines += ["", "## Not controlled", "",
              "- The model's own randomness: the same request does not give the same run twice.",
              "- Tokens and cost are each vendor's own count.",
              "- The agent can read its own credential in its home folder.",
              "- The system prompt and the tool descriptions are each command line's own.", ""]
    return "\n".join(lines)
