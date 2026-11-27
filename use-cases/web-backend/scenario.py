"""Record one request to the order service, and compute what happened in it.

    python scenario.py /tmp/web-backend

The folder gets the program, `orders.db` and the recording `r1` of
`python main.py` (one `GET /customers/3/orders` through the test client).
Then the same program runs again in another copy, without Ormaos, under
`sys.settrace` and with a trace callback on every sqlite3 connection; the
answers in `questions.json` come from that second execution.

Needs, in the Python that runs it: ormaos, and the requirements.txt.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "requirements.txt", "store.py", "app.py", "main.py"]


def main():
    args = common.arguments(__doc__)
    common.need("fastapi", "httpx")
    common.copy_program(HERE, args.target, FILES)
    common.record(args.target, "python", "main.py")

    found = common.trace(HERE, FILES, "main.py")
    # The statements of the request: everything a connection ran that was
    # not caused by store.create.
    request = [s for s in found["sql"] if s["fn"] != "create" and s["sql"] != "(connect)"]
    selects = [s for s in request if s["sql"].startswith("SELECT")]
    by_function = {}
    for statement in selects:
        by_function[statement["fn"]] = by_function.get(statement["fn"], 0) + 1
    most = max(by_function, key=by_function.get)
    caught = [e for e in found["exceptions"] if e["handled_in"]]

    questions = [
        {
            "id": "q1",
            "question": "How many SQL SELECT statements ran while the request GET /customers/3/orders was handled?",
            "answer": len(selects),
            "oracle": "sqlite3 trace callback on every connection",
        },
        {
            "id": "q2",
            "question": "How many times did the SELECT on the table order_items run, and in which function?",
            "answer": {
                "times": sum(1 for s in selects if "FROM order_items" in s["sql"]),
                "function": sorted({s["fn"] for s in selects if "FROM order_items" in s["sql"]}),
            },
            "oracle": "sqlite3 trace callback, with the function of the program on the stack",
        },
        {
            "id": "q3",
            "question": "Which function of the program ran the most SELECT statements during the request, and how many?",
            "answer": {"function": most, "times": by_function[most]},
            "oracle": "sqlite3 trace callback, with the function of the program on the stack",
        },
        {
            "id": "q4",
            "question": "How many times was order_total called?",
            "answer": len(common.calls(found, "order_total")),
            "oracle": "sys.settrace",
        },
        {
            "id": "q5",
            "question": "Did product_names run?",
            "answer": len(common.calls(found, "product_names")) > 0,
            "oracle": "sys.settrace",
        },
        {
            "id": "q6",
            "question": "How many sqlite3 connections did the whole execution open?",
            "answer": sum(1 for s in found["sql"] if s["sql"] == "(connect)"),
            "oracle": "a wrapper around sqlite3.connect",
        },
        {
            "id": "q7",
            "question": "Which exceptions were raised and handled inside the program, and in which function was each handled?",
            "answer": [{"type": e["type"], "handled_in": e["handled_in"]} for e in caught],
            "oracle": "sys.settrace exception events",
        },
    ]
    show = ["ormaos", "io", common.address(args.target, "r1", "list_orders"), "--kind", "sqlite"]
    common.finish(args, HERE, "web-backend", ["r1"], questions, show)


if __name__ == "__main__":
    main()
