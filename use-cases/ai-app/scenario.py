"""Record one run of the ticket summaries, and compute what happened in it.

    python scenario.py /tmp/ai-app

The folder gets the program, `summaries.json` and the recording `r1` of
`python app.py`. Then the same program runs again in another copy, without
Ormaos, under `sys.settrace`; the answers in `questions.json` come from the
calls seen there, among them what the model server itself was asked
(`generate(model, prompt)`) and what it answered.

Needs, in the Python that runs it: ormaos.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "app.py", "model_server.py", "tickets.json"]
SHOW = ["ormaos", "io", "r1", "--kind", "http"]


def main():
    args = common.arguments(__doc__)
    common.copy_program(HERE, args.target, FILES)
    common.record(args.target, "python", "app.py")

    found = common.trace(HERE, FILES, "app.py")
    served = common.calls(found, "generate")
    by_model = {}
    by_status = {}
    for call in served:
        model = call["args"]["model"]["value"]
        by_model[model] = by_model.get(model, 0) + 1
    statuses = [
        c["args"]["code"]["value"]
        for c in found["calls"]
        if c["fn"] == "Handler.reply"
    ]
    for status in statuses:
        by_status[str(status)] = by_status.get(str(status), 0) + 1
    summaries = common.calls(found, "summarize")
    twice = [
        n
        for n, call in enumerate(summaries, 1)
        if sum(1 for c in common.calls(found, "ask") if c["parent"] == call["id"]) > 1
    ]
    caught = {}
    for exc in found["exceptions"]:
        if exc["handled_in"] == "summarize":
            caught[exc["type"]] = caught.get(exc["type"], 0) + 1
    written = [o for o in found["opens"] if "w" in o["mode"]]

    questions = [
        {
            "id": "q1",
            "question": "How many HTTP requests did the model server receive?",
            "answer": len(served),
            "oracle": "sys.settrace on the server's generate function",
        },
        {
            "id": "q2",
            "question": "How many requests were answered with each HTTP status?",
            "answer": dict(sorted(by_status.items())),
            "oracle": "sys.settrace on the server's reply function, its status argument",
        },
        {
            "id": "q3",
            "question": "How many requests went to each model?",
            "answer": dict(sorted(by_model.items())),
            "oracle": "sys.settrace on the server's generate function, its model argument",
        },
        {
            "id": "q4",
            "question": "Which exceptions were handled in summarize, and how many of each?",
            "answer": caught,
            "oracle": "sys.settrace exception events",
        },
        {
            "id": "q5",
            "question": "Which calls of summarize, counted from 1 in order, called ask more than once?",
            "answer": twice,
            "oracle": "sys.settrace, the calls made from each summarize",
        },
        {
            "id": "q6",
            "question": "How many times did ask run?",
            "answer": len(common.calls(found, "ask")),
            "oracle": "sys.settrace",
        },
        {
            "id": "q7",
            "question": "Which files of the folder did the program open for writing, and from which function?",
            "answer": [{"file": o["path"], "function": o["fn"]} for o in written],
            "oracle": "a wrapper around builtins.open",
        },
    ]
    common.finish(args, HERE, "ai-app", ["r1"], questions, SHOW)


if __name__ == "__main__":
    main()
