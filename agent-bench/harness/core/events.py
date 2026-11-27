"""The one record of a run, the same for every agent: a JSONL file of
events. ``EVENTS.md`` describes it; this file checks it.

An adapter turns what its command line prints into these events. The
runner numbers and times them, and ends every stream with exactly one
``final`` and one ``usage``. Results, reports and pages read these events
and never the command line's own output.
"""

import json

VERSION = 1
NUMBER = (int, float)
OPTIONAL_NUMBER = (int, float, type(None))
REASONS = ("done", "error", "time_limit", "no_result")
# type -> {field: types}
FIELDS = {
    "start": {"agent": str, "cli_version": (str, type(None)), "model": (str, type(None)),
              "tools": list, "extensions": list},
    "assistant_text": {"text": str},
    "tool_call": {"id": (str, type(None)), "tool": str, "kind": str, "input": dict},
    "tool_result": {"id": (str, type(None)), "is_error": bool, "output": str},
    "final": {"text": str, "is_error": bool, "reason": str},
    "usage": {"input_tokens": OPTIONAL_NUMBER, "output_tokens": OPTIONAL_NUMBER,
              "cache_read_tokens": OPTIONAL_NUMBER, "cache_write_tokens": OPTIONAL_NUMBER,
              "cost_usd": OPTIONAL_NUMBER, "turns": OPTIONAL_NUMBER, "wall_seconds": NUMBER},
}
KINDS = ("shell", "file", "other")
EMPTY_USAGE = {"input_tokens": None, "output_tokens": None, "cache_read_tokens": None,
               "cache_write_tokens": None, "cost_usd": None, "turns": None}


def is_a(value, types):
    allowed = types if isinstance(types, tuple) else (types,)
    return isinstance(value, allowed) and not (isinstance(value, bool) and bool not in allowed)


def problems(event):
    """What is wrong with one event; an empty list when nothing is."""
    if not isinstance(event, dict):
        return ["not an object"]
    kind = event.get("type")
    if kind not in FIELDS:
        return [f"unknown type {kind!r}"]
    wrong = []
    expected = {"v": int, "seq": int, "t": NUMBER, "type": str, **FIELDS[kind]}
    for field, types in expected.items():
        if field not in event:
            wrong.append(f"{kind}: no {field!r}")
        elif not is_a(event[field], types):
            wrong.append(f"{kind}: {field!r} is {type(event[field]).__name__}")
    wrong += [f"{kind}: unknown field {field!r}" for field in event if field not in expected]
    if event.get("v") != VERSION:
        wrong.append(f"version {event.get('v')!r}")
    if kind == "tool_call" and event.get("kind") not in KINDS:
        wrong.append(f"tool_call: kind {event.get('kind')!r}")
    if kind == "final" and event.get("reason") not in REASONS:
        wrong.append(f"final: reason {event.get('reason')!r}")
    return wrong


def stream_problems(events):
    """What is wrong with a whole stream."""
    wrong = [f"event {n}: {p}" for n, event in enumerate(events) for p in problems(event)]
    if [e.get("seq") for e in events] != list(range(len(events))):
        wrong.append("seq is not 0, 1, 2, ...")
    kinds = [e.get("type") for e in events]
    if kinds.count("final") != 1 or kinds.count("usage") != 1 or kinds[-2:] != ["final", "usage"]:
        wrong.append("the stream does not end with one final and one usage")
    return wrong


def read(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class Writer:
    """Writes the events of one run: numbers them, times them, and closes
    the stream with one ``final`` and one ``usage``."""

    def __init__(self, handle, clock):
        self.handle, self.clock = handle, clock
        self.seq = 0
        self.final = None
        self.usage = None

    def _write(self, event):
        event = {"v": VERSION, "seq": self.seq, "t": round(self.clock(), 3), **event}
        self.handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        self.handle.flush()
        self.seq += 1

    def add(self, event):
        if event["type"] == "final":
            self.final = self.final or event  # the first one counts
        elif event["type"] == "usage":
            self.usage = event
        elif self.final is None:
            self._write(event)

    def close(self, wall_seconds, timed_out):
        final = self.final
        if timed_out:  # the time limit is the harness's, whatever the command line said
            final = {"type": "final", "text": (final or {}).get("text", ""), "is_error": True, "reason": "time_limit"}
        elif final is None:
            final = {"type": "final", "text": "", "is_error": True, "reason": "no_result"}
        self._write(final)
        self._write({**EMPTY_USAGE, **(self.usage or {}), "type": "usage", "wall_seconds": round(wall_seconds, 1)})


def summary(events, allowed_tools):
    """What a result line says of a run: everything in it comes from the
    events. ``allowed_tools`` is {tool: kind} of the adapter."""
    start = next((e for e in events if e["type"] == "start"), None)
    final = next(e for e in events if e["type"] == "final")
    usage = next(e for e in events if e["type"] == "usage")
    calls = [e for e in events if e["type"] == "tool_call"]
    tools = {}
    for call in calls:
        tools[call["tool"]] = tools.get(call["tool"], 0) + 1
    violations = []
    if start is None:
        violations.append("the command line did not say what it started with")
    else:
        extra = sorted(set(start["tools"]) - set(allowed_tools))
        if extra:
            violations.append("tools beyond shell and files: " + ", ".join(extra))
        if start["extensions"]:
            violations.append("extensions connected: " + ", ".join(map(str, start["extensions"])))
    other = sorted({call["tool"] for call in calls if call["kind"] == "other"})
    if other:
        violations.append("called tools beyond shell and files: " + ", ".join(other))
    tokens = {"input": usage["input_tokens"], "output": usage["output_tokens"],
              "cache_read": usage["cache_read_tokens"], "cache_write": usage["cache_write_tokens"]}
    return {
        "wall_seconds": usage["wall_seconds"],
        "timed_out": final["reason"] == "time_limit",
        "final": final["reason"],
        "error": None if final["reason"] == "done" else f"{final['reason']}: {final['text']}"[:200],
        "tool_calls": len(calls),
        "tools": tools,
        "turns": usage["turns"],
        "tokens": tokens if any(v is not None for v in tokens.values()) else None,
        "cost_usd": usage["cost_usd"],
        "model": start["model"] if start else None,
        "cli_version": start["cli_version"] if start else None,
        "violations": violations,
    }
