"""The rules of knows2: those of ``../knows/grade.py`` and three more, for
the formats the question writer asked for.

- ``word``: one of a few given words; compared without spaces and quotes
  around it and without regard to capitals.
- ``{"round": n}``: a number, or a string that reads as one; equal after
  rounding both to ``n`` decimals.
- ``{"parts": [rule, ...]}``: several values in one answer, as a string with
  commas between them ("7, no") or as a list; each part by its rule.

``rules.json`` has the rule of every question the writer wrote, the dropped
ones too. Importing this file makes ``grade`` use these rules.
"""

import json
from pathlib import Path

import grade

HERE = Path(__file__).resolve().parent
ALL = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))
DROPPED = json.loads((HERE / "dropped.json").read_text(encoding="utf-8")) if (HERE / "dropped.json").exists() else {}
RULES = {name: {qid: rule for qid, rule in rules.items() if qid not in DROPPED.get(name, {})}
         for name, rules in ALL.items()}
knows_same = grade.same


def same(rule, given, oracle, mount=""):
    if rule == "word":
        clean = lambda text: text.strip().strip("`'\"").strip().lower()  # noqa: E731
        return isinstance(given, str) and clean(given) == clean(oracle)
    if isinstance(rule, dict) and "round" in rule:
        mine, theirs = grade.norm("number", given), grade.norm("number", oracle)
        return mine is not grade.MISSING and round(mine, rule["round"]) == round(theirs, rule["round"])
    if isinstance(rule, dict) and "parts" in rule:
        if isinstance(given, str):
            given = [part.strip() for part in given.split(",")]
        return (isinstance(given, list) and len(given) == len(rule["parts"])
                and all(same(r, g, o, mount) for r, g, o in zip(rule["parts"], given, oracle)))
    return knows_same(rule, given, oracle, mount)


grade.same = same
grade.RULES = RULES
