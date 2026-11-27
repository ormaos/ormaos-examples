"""Record one run of the revenue report, and compute what happened in it.

    python scenario.py /tmp/data-pipeline

The folder gets the program, its two CSV files, `report.csv` and the
recording `r1` of `python pipeline.py`. Then the same program runs again in
another copy, without Ormaos, under `sys.settrace`; the rows, columns and
nulls of every DataFrame that entered or left a function are counted there,
and the answers in `questions.json` come from those counts.

Needs, in the Python that runs it: ormaos, and the requirements.txt.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import common  # noqa: E402

FILES = ["README.md", "requirements.txt", "pipeline.py", "orders.csv", "customers.csv"]
SHOW = ["ormaos", "tree", "r1", "--function", "join_customers"]


def main():
    args = common.arguments(__doc__)
    common.need("pandas")
    common.copy_program(HERE, args.target, FILES)
    common.record(args.target, "python", "pipeline.py")

    found = common.trace(HERE, FILES, "pipeline.py")
    one = lambda name: common.calls(found, name)[0]  # noqa: E731
    loaded = one("load_orders")["result"]
    priced = one("drop_unpriced")
    join = one("join_customers")
    written = [o for o in found["opens"] if "w" in o["mode"]]

    questions = [
        {
            "id": "q1",
            "question": "How many rows and how many nulls had the DataFrame that load_orders returned?",
            "answer": {"rows": loaded["rows"], "nulls": loaded["nulls"]},
            "oracle": "sys.settrace return event, DataFrame.shape and isna().sum()",
        },
        {
            "id": "q2",
            "question": "How many rows went into drop_unpriced and how many came out?",
            "answer": {"in": priced["args"]["orders"]["rows"], "out": priced["result"]["rows"]},
            "oracle": "sys.settrace call and return events, DataFrame.shape",
        },
        {
            "id": "q3",
            "question": "How many rows of orders went into join_customers and how many rows came out?",
            "answer": {"in": join["args"]["orders"]["rows"], "out": join["result"]["rows"]},
            "oracle": "sys.settrace call and return events, DataFrame.shape",
        },
        {
            "id": "q4",
            "question": "How many columns had the DataFrame that join_customers returned?",
            "answer": len(join["result"]["columns"]),
            "oracle": "sys.settrace return event, DataFrame.columns",
        },
        {
            "id": "q5",
            "question": "Did drop_repeats run?",
            "answer": len(common.calls(found, "drop_repeats")) > 0,
            "oracle": "sys.settrace",
        },
        {
            "id": "q6",
            "question": "How many rows had the DataFrame passed to write_report?",
            "answer": one("write_report")["args"]["report"]["rows"],
            "oracle": "sys.settrace call event, DataFrame.shape",
        },
        {
            "id": "q7",
            "question": "Which files of the folder did the program open for writing, and from which function?",
            "answer": [{"file": o["path"], "function": o["fn"]} for o in written],
            "oracle": "a wrapper around builtins.open",
        },
    ]
    common.finish(args, HERE, "data-pipeline", ["r1"], questions, SHOW)


if __name__ == "__main__":
    main()
