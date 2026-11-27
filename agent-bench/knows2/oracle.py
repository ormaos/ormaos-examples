"""The answer of every question of ``writer/<task>/questions.json``, from the
independent execution under the tracer of ``tracer.py``.

``answers(name, found, folder)`` gives ``{id: answer}``. ``found`` is what
the tracer wrote (for agent-change ``{"r1": ..., "r2": ...}``), ``folder``
the copy of the program that execution ran in; its source files are read to
tell which line of a function is which. Nothing here reads a recording of
Ormaos or a trace of VizTracer.

An answer is a ``Dropped`` when the oracle cannot give one unambiguous
answer: the question is then left out of the task, with the reason.
"""

import json


class Dropped:
    def __init__(self, reason):
        self.reason = reason


def calls(found, name, file=None):
    """The calls of a function, in order; `name` is the end of its qualified name."""
    return [c for c in found["calls"]
            if (c["fn"] == name or c["fn"].endswith("." + name)) and file in (None, c["file"])]


def one(found, name, file=None):
    mine = calls(found, name, file)
    if len(mine) != 1:
        raise SystemExit(f"oracle: {len(mine)} calls of {name}, expected 1")
    return mine[0]


def children(found, call, name, file=None):
    return [c for c in calls(found, name, file) if c["parent"] == call["id"]]


def value(described):
    return described["json"]


def ran(call, folder, text):
    """How many times the call ran a line of its file that has `text`."""
    source = (folder / call["file"]).read_text(encoding="utf-8").splitlines()
    return sum(1 for line in call["lines"] if text in source[line - 1])


# --------------------------------------------------------------------------


def web_backend(found, folder):
    listed = one(found, "list_orders")
    body = value(listed["result"])
    orders = body["orders"]
    totals = [order["total_cents"] for order in orders]
    top = [order for order in orders if order["total_cents"] == max(totals)]
    through_except = any(e["type"].endswith("KeyError") and e["handled_in"] == "discount_for"
                         for e in found["exceptions"])
    during = ("list_orders", "find_customer", "items_of", "price_of", "product_names", "order_total")
    return {
        "q1": body["customer"],
        "q2": [value(one(found, "discount_for")["result"]), through_except],
        "q3": orders[0]["id"],
        "q4": sum(totals),
        "q5": [top[0]["id"], top[0]["total_cents"]] if len(top) == 1
        else Dropped(f"{len(top)} orders share the largest total_cents"),
        "q6": len(calls(found, "price_of")),
        "q7": sum(1 for s in found["sql"] if s["fn"] in during and s["sql"] != "(connect)"),
        "q8": sum(1 for s in found["sql"] if s["fn"] == "create" and s["sql"].startswith("INSERT INTO order_items")),
    }


def data_pipeline(found, folder):
    loaded = one(found, "load_orders")["result"]
    priced = one(found, "drop_unpriced")
    join = one(found, "join_customers")
    known = {row["customer_id"] for row in value(join["args"]["customers"])["rows"]}
    report = value(one(found, "write_report")["args"]["report"])["rows"]
    return {
        "q1": loaded["rows"],
        "q2": priced["args"]["orders"]["rows"] - priced["result"]["rows"],
        "q3": len(calls(found, "drop_repeats")) > 0,
        "q4": join["args"]["orders"]["rows"],
        "q5": join["result"]["rows"],
        "q6": sum(1 for row in value(join["args"]["orders"])["rows"] if row["customer_id"] not in known),
        "q7": [report[0]["region"], report[0]["amount"]],
        "q8": round(sum(row["amount"] for row in report), 2),
    }


def notebook(found, folder):
    book = json.loads((folder / "report.ipynb").read_text(encoding="utf-8"))
    code = [cell for cell in book["cells"] if cell["cell_type"] == "code"]
    loaded = value(one(found, "load")["result"])
    drop, tax, total = one(found, "drop_key_accounts"), one(found, "add_tax"), one(found, "total")
    taxed_first = tax["id"] < drop["id"]
    limit = 1000
    if taxed_first:
        taxed = value(tax["result"])
        if len(taxed) != len(loaded):
            raise SystemExit("oracle: add_tax did not keep the rows of load")
        lost = sum(1 for before, after in zip(loaded, taxed) if before["price"] <= limit < after["price"])
    else:
        lost = 0
    last = value(total["args"]["rows"])
    return {
        "q1": len(loaded),
        "q2": code[found["cells"][2]["cell"] - 1]["id"],
        "q3": "tax-inclusive" if taxed_first else "pre-tax",
        "q4": drop["result"]["len"],
        "q5": lost,
        "q6": round(value(total["result"]), 2),
        "q7": round(max(row["price"] for row in last), 2),
        "q8": sum(row["quantity"] for row in last),
    }


def ml_training(found, folder):
    steps = calls(found, "train_step")
    skipped = [n for n, step in enumerate(steps) if step["result"]["type"] == "NoneType"]
    batches = [value(step["args"]["batch"])["values"] for step in steps]
    columns = ["distance", "parcels", "hour", "weekend"]
    constant = sorted({columns[c] for n in skipped for c in range(4) if len({row[c] for row in batches[n]}) == 1})
    flags = sorted({row[3] for n in skipped for row in batches[n]})
    data = value(one(found, "make_data")["result"])[0]["values"]
    return {
        "q1": len(calls(found, "apply_update")),
        "q2": len(skipped),
        "q3": skipped,
        "q4": constant[0] if len(constant) == 1
        else Dropped(f"{len(constant)} columns were constant within a skipped batch"),
        "q5": sum(1 for row in data if row[3] == 1.0),
        "q6": max(n for n in range(len(steps)) if n not in skipped),
        "q7": flags[0] if len(flags) == 1
        else Dropped(f"the weekend flag took {len(flags)} values in the skipped batches"),
        "q8": sum(1 for rows in batches if len({row[3] for row in rows}) == 2),
    }


def rl_env(found, folder):
    episodes = calls(found, "run_episode")
    ends = [c for c in found["calls"] if c["fn"] in ("ended_at_goal", "ended_at_limit")]
    at_limit = [n for n, end in enumerate(ends, 1) if end["fn"] == "ended_at_limit"]
    lengths = [len(children(found, episode, "step")) for episode in episodes]
    return {
        "q1": sum(1 for end in ends if end["fn"] == "ended_at_goal"),
        "q2": len(calls(found, "_arrival_bonus")),
        "q3": len(calls(found, "_bump")),
        "q4": len(calls(found, "step")),
        "q5": at_limit[0] if len(at_limit) == 1
        else Dropped(f"{len(at_limit)} episodes ended at the step limit, the question asks for one"),
        "q6": min(lengths),
        "q7": sum(1 for c in calls(found, "choose") if c["result"].get("value") == "right"),
        "q8": round(max(value(end["args"]["total"]) for end in ends), 1),
    }


def ai_app(found, folder):
    summaries = calls(found, "summarize")
    asked = calls(found, "ask")
    twice = [s for s in summaries if len(children(found, s, "ask")) > 1]
    written = value(one(found, "save")["args"]["summaries"])
    return {
        "q1": Dropped("the server listens on a free port the system picks (`(\"127.0.0.1\", 0)`): "
                      "the oracle's execution and the execution of each arm got different ports"),
        "q2": len(summaries) - len(twice),
        "q3": sum(1 for c in calls(found, "Handler.reply") if c["args"]["code"]["value"] == 503),
        "q4": len(asked),
        "q5": [value(s["args"]["ticket"])["id"] for s in twice],
        "q6": max(len(c["args"]["prompt"]["value"]) for c in asked),
        "q7": written[0]["summary"],
        "q8": (folder / "summaries.json").stat().st_size,
    }


def agent_change(found, folder):
    r1, r2 = found["r1"], found["r2"]

    def rows(run, name):
        return next(value(c["args"]["rows"]) for c in calls(run, "write_rows")
                    if c["args"]["name"]["value"] == name)

    before, after = rows(r1, "invoices.csv"), rows(r2, "invoices.csv")
    inexact = 0
    for call in calls(r2, "line_price"):
        (discount,) = children(r2, call, "discount_percent")
        inexact += value(call["locals"]["price"]) * (100 - discount["result"]["value"]) % 100 != 0
    refunds = [row[1] for row in rows(r2, "refunds.csv")]
    return {
        "q1": len(calls(r1, "line_price")),
        "q2": sum(1 for o in r2["opens"] if o["path"] == "tiers.json"),
        "q3": sum(row[2] for row in before),
        "q4": sum(row[2] for row in after),
        "q5": sum(1 for a, b in zip(before, after) if a[2] != b[2]),
        "q6": sum(1 for c in calls(r2, "discount_percent") if c["result"]["value"] == 10),
        "q7": inexact,
        "q8": refunds if len(refunds) == 3 else Dropped(f"refunds.csv got {len(refunds)} rows, not three"),
    }


def order_sync(found, folder):
    sync = one(found, "sync_orders")
    # A call that an exception left has the result None, like one that returns nothing.
    applied = [c for c in calls(found, "apply_order") if c["result"]["type"] == "bool"]
    new = [c for c in applied if c["result"]["value"] is True]
    by_id = {c["id"]: c for c in found["calls"]}
    handled = [e for e in found["exceptions"] if e.get("handled_call") == sync["id"]]
    skipped = []
    for error in handled:  # the order of the call of sync_orders the exception came out of
        call = by_id[error["raised_call"]]
        while call["parent"] != sync["id"]:
            call = by_id[call["parent"]]
        skipped.append(value(call["args"]["order"])["order_id"])
    short = [c for c in new if value(c["locals"]["taken"]) < value(c["locals"]["wanted"])]
    return {
        "q1": one(found, "parse_rows")["result"]["len"],
        "q2": len(new),
        "q3": len(applied) - len(new),
        "q4": len(handled),
        "q5": sorted(skipped),
        "q6": {order: e["type"].rsplit(".", 1)[-1] for order, e in zip(skipped, handled)}
        if len(set(skipped)) == len(skipped) else Dropped("an order id was skipped twice"),
        "q7": sum(value(c["locals"]["taken"]) for c in new),
        "q8": [len(short), sum(value(c["locals"]["wanted"]) - value(c["locals"]["taken"]) for c in short)],
    }


def freight_quote(found, folder):
    prices = calls(found, "price", "job.py")
    from_card = [p for p in prices if children(found, p, "rate", "ratecard.py")]
    asked = calls(found, "rate", "carrier.py")
    served = calls(found, "RatesHandler.do_GET")
    if len(asked) != len(served) or len(asked) != len(prices):
        raise SystemExit("oracle: freight-quote: not one request per shipment")
    written = value(one(found, "replace_all")["args"]["rows"])
    refused = lambda code: [value(a["args"]["shipment"])["shipment_id"]  # noqa: E731
                            for a, s in zip(asked, served) if ran(s, folder, f"send_error({code})")]
    return {
        "q1": len(written),
        "q2": len(prices) - len(from_card),
        "q3": len(from_card),
        "q4": len(refused(429)),
        "q5": value(from_card[0]["args"]["shipment"])["shipment_id"] if from_card else "none",
        "q6": refused(422),
        "q7": sum(ran(s, folder, 'state["calls_used_today"] += 1') for s in served),
        "q8": sum(row["amount_cents"] for row in written),
    }


BY_TASK = {
    "web-backend": web_backend, "data-pipeline": data_pipeline, "notebook": notebook,
    "ml-training": ml_training, "rl-env": rl_env, "ai-app": ai_app, "agent-change": agent_change,
    "order-sync": order_sync, "freight-quote": freight_quote,
}


def answers(name, found, folder):
    return BY_TASK[name](found, folder)
