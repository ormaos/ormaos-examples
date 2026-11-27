"""The nine tasks: for each, the execution, what its folder keeps, and its
questions.

Seven are the programs of ``use-cases/``, each with the execution that its
``scenario.py`` records and the questions of its ``questions.json``. Two are
the jobs ``order-sync`` and ``freight-quote`` on the night that the scenarios
of ``agent-bench/bugs/`` play; their questions are in this file, and their
answers are computed by the tracer of ``use-cases/common.py`` in one more
copy of that night, never from a recording.
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
REPO = BENCH.parent
USE_CASES = REPO / "use-cases"
sys.path.insert(0, str(BENCH))
import benchlib  # noqa: E402

GIT = ["git", "-c", "user.name=dev", "-c", "user.email=dev@example.com"]


def simple(script):
    def play(stage):
        stage.execute([script])
    return play


def play_notebook(stage):
    # The cells record themselves (`with ormaos.record():`), so the session
    # is not put under `ormaos run`; under VizTracer it is, like any other.
    stage.execute(["/opt/knows/session.py"], recorder=False)


def play_agent_change(stage):
    """A repository with two commits, and `run.py` at each of them."""
    folder = stage.folder
    stage.sh(["git", "init", "-q", "-b", "main", "."])
    (folder / ".gitignore").write_text(".ormaos/\n__pycache__/\ninvoices.csv\nrefunds.csv\n")
    # What an arm adds is kept out of the commits, the same way in every arm.
    with open(folder / ".git" / "info" / "exclude", "a", encoding="utf-8") as exclude:
        exclude.write(".venv\nresult-r1.json\nresult-r2.json\nquestions.json\nanswers.json\n")
    stage.sh([*GIT, "add", "-A"])
    stage.sh([*GIT, "commit", "-q", "-m", "Add the billing tool"])
    stage.execute(["run.py"], label="r1")
    stage.sh(["git", "apply", "/opt/use-cases/agent-change/change.patch"])
    stage.sh([*GIT, "add", "-A"])
    stage.sh([*GIT, "commit", "-q", "-m", "Give gold and silver customers their discount on invoices"])
    stage.execute(["run.py"], label="r2")


def play_job(stage):
    """The nights of agent-bench/bugs/<job>/scenario.py; the last one is the execution."""
    stage.story = benchlib.scenario(stage.name)
    done = stage.story.play(stage)
    if not benchlib.said_ok(done, stage.story.SAYS):
        raise SystemExit(f"{stage.name}/{stage.arm}: the night did not say OK:\n{done.stdout}{done.stderr}")


# --------------------------------------------------------------------------
# The questions of the two jobs. `found` is what the tracer of
# use-cases/common.py saw in that night's run.
# --------------------------------------------------------------------------


def _calls(found, name, file=None):
    return [c for c in found["calls"]
            if (c["fn"] == name or c["fn"].endswith("." + name)) and file in (None, c["file"])]


def _handled(found, function):
    counts = {}
    for exc in found["exceptions"]:
        if exc["handled_in"] == function:
            counts[exc["type"]] = counts.get(exc["type"], 0) + 1
    return counts


def questions_order_sync(found):
    applied = [c["result"]["value"] for c in _calls(found, "apply_order") if "result" in c]
    return [
        ("q1", "Which of the functions from_csv and from_api ran?",
         sorted(name for name in ("from_csv", "from_api") if _calls(found, name))),
        ("q2", "How many orders did parse_rows return?", _calls(found, "parse_rows")[0]["result"]["len"]),
        ("q3", "How many times did check_order run, and how many times apply_order?",
         {"check_order": len(_calls(found, "check_order")), "apply_order": len(_calls(found, "apply_order"))}),
        ("q4", "Which exceptions were handled in sync_orders, and how many of each?",
         _handled(found, "sync_orders")),
        ("q5", "In which functions were the exceptions raised that sync_orders handled?",
         sorted({e["raised_in"] for e in found["exceptions"] if e["handled_in"] == "sync_orders"})),
        ("q6", "How many calls of apply_order returned True, and how many False?",
         {"true": applied.count(True), "false": applied.count(False)}),
        ("q7", "How many times did check_quantity run?", len(_calls(found, "check_quantity"))),
    ]


def questions_freight_quote(found):
    prices = _calls(found, "price", "job.py")
    card = _calls(found, "rate", "ratecard.py")
    from_card = [n for n, call in enumerate(prices, 1) if any(c["parent"] == call["id"] for c in card)]
    return [
        ("q1", "How many times did the function rate of carrier.py run, and how many times the function rate of ratecard.py?",
         {"carrier.py": len(_calls(found, "rate", "carrier.py")), "ratecard.py": len(card)}),
        ("q2", "Which exceptions were handled in price, and how many of each?", _handled(found, "price")),
        ("q3", "How many times did tariff_price run?", len(_calls(found, "tariff_price"))),
        ("q4", "Which calls of price, counted from 1 in order, called the function rate of ratecard.py?", from_card),
        ("q5", "How many quotes did replace_all receive?", _calls(found, "replace_all")[0]["args"]["rows"]["len"]),
        ("q6", "How many times was data/carrier.json opened for writing?",
         sum(1 for o in found["opens"] if o["path"] == "data/carrier.json" and "w" in o["mode"])),
        ("q7", "How many times did RatesHandler.do_GET run?", len(_calls(found, "RatesHandler.do_GET"))),
    ]


# --------------------------------------------------------------------------

USE_CASE_FILES = {
    "web-backend": ["README.md", "requirements.txt", "store.py", "app.py", "main.py"],
    "data-pipeline": ["README.md", "requirements.txt", "pipeline.py", "orders.csv", "customers.csv"],
    "notebook": ["README.md", "requirements.txt", "report.ipynb", "sales.csv", "run_notebook.py"],
    "ml-training": ["README.md", "requirements.txt", "train.py"],
    "rl-env": ["README.md", "env.py", "run.py"],
    "ai-app": ["README.md", "app.py", "model_server.py", "tickets.json"],
    "agent-change": ["README.md", "billing.py", "run.py", "orders.json", "returns.json", "tiers.json"],
}

# what: the execution, in one sentence, the same in every arm.
# install: what pip installs for the program (None: the standard library).
# removed: the input files that execution read, taken out of the folder.
# scripts, modules: how a tool call is read as running the program again.
TASKS = {
    "web-backend": dict(
        play=simple("main.py"), install=["-r", "/opt/use-cases/web-backend/requirements.txt"],
        what="`.venv/bin/python main.py` ran once in this folder.",
        removed=[], scripts=["main.py"], modules=["app", "store", "main"]),
    "data-pipeline": dict(
        play=simple("pipeline.py"), install=["-r", "/opt/use-cases/data-pipeline/requirements.txt"],
        what="`.venv/bin/python pipeline.py` ran once in this folder.",
        removed=["orders.csv", "customers.csv"], scripts=["pipeline.py"], modules=["pipeline"]),
    "notebook": dict(
        play=play_notebook, install=["-r", "/opt/use-cases/notebook/requirements.txt"],
        what="The code cells of report.ipynb ran once in a Jupyter kernel of `.venv/bin/python`, "
             "in this folder, in the order of the execution counts saved in the notebook.",
        removed=["sales.csv"], scripts=["run_notebook.py", "report.ipynb"], modules=["nbclient", "nbformat"]),
    "ml-training": dict(
        play=simple("train.py"), install=["torch", "--index-url", "https://download.pytorch.org/whl/cpu"],
        what="`.venv/bin/python train.py` ran once in this folder.",
        removed=[], scripts=["train.py"], modules=["train"]),
    "rl-env": dict(
        play=simple("run.py"), install=None,
        what="`python3 run.py` ran once in this folder.",
        removed=[], scripts=["run.py"], modules=["env", "run"]),
    "ai-app": dict(
        play=simple("app.py"), install=None,
        what="`python3 app.py` ran once in this folder.",
        removed=["tickets.json"], scripts=["app.py"], modules=["app", "model_server"]),
    "agent-change": dict(
        play=play_agent_change, install=None,
        what="This folder is a git repository with two commits. `python3 run.py` ran once at the first "
             "commit (that execution is r1) and once at the second (r2).",
        removed=[], scripts=["run.py"], modules=["billing", "run"], labels=["r1", "r2"]),
    "order-sync": dict(
        play=play_job, install=None, job=True, questions=questions_order_sync,
        what="Last night cron ran `python3 job.py --source api` in this folder; since then the sales "
             "system has replaced its orders with today's.",
        removed=[], scripts=["job.py"], modules=["job", "fetch", "parse", "validate", "inventory"]),
    "freight-quote": dict(
        play=play_job, install=None, job=True, questions=questions_freight_quote,
        what="Last night cron ran `python3 job.py` in this folder; since then the dispatch list has been "
             "replaced with today's and the carrier's count of calls has started again.",
        removed=[], scripts=["job.py"], modules=["job", "carrier", "ratecard", "quotes", "shipments"]),
}
NAMES = list(TASKS)


def copy_program(name, folder):
    """The program as its scenario copies it, in a new folder."""
    if TASKS[name].get("job"):
        story = benchlib.scenario(name)
        shutil.copytree(story.SOURCE, folder, ignore=shutil.ignore_patterns(*story.NOT_COPIED))
        return
    folder.mkdir(parents=True)
    for file in USE_CASE_FILES[name]:
        shutil.copy2(USE_CASES / name / file, folder / file)


def committed_questions(name):
    """The questions of a use case with their answers, as its scenario.py wrote them."""
    document = json.loads((USE_CASES / name / "questions.json").read_text(encoding="utf-8"))
    return [(q["id"], q["question"], q["answer"]) for q in document["questions"]]


def prompt(name, arm):
    """The task: the same text in every arm, plus one sentence for the arm."""
    task = TASKS[name]
    text = task["what"] + " The folder is as that left it"
    if task["removed"]:
        text += ", without the input it read (" + ", ".join(task["removed"]) + ")"
    text += (
        ". questions.json has questions about what happened in "
        + ("those executions" if task.get("labels") else "that execution")
        + ". Write answers.json in this folder: one JSON object with the id of every question as a key "
        "and, under it, the answer in the format the question gives. Answer what happened then; give "
        "null for an answer you cannot find out."
    )
    traces = [f"result-{label}.json" for label in task.get("labels", [])] or ["result.json"]
    if arm == "raw":
        text += (
            f" A VizTracer trace of {'each execution' if len(traces) > 1 else 'that execution'} is in "
            f"{' and '.join(traces)}, in the Chrome Trace Event format"
            ' (JSON; "traceEvents" has one entry per function call, with its name,'
            ' its start "ts" and its duration "dur" in microseconds); read it with python3.'
        )
    elif arm == "ormaos":
        text += (
            f" {'Those executions were' if len(traces) > 1 else 'That execution was'} recorded with Ormaos: "
            "the recording is in .ormaos/ and the command line is .venv/bin/ormaos;"
            ' run ".venv/bin/ormaos guide" first.'
        )
    return text
