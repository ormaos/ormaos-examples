"""Grade an answers.json against the oracle answers.

    python3 grade.py <task> <answers.json>

Every question has a rule, written in rules.json before any run. An answer
is right or wrong as a whole; the score of a run is the share of its
questions that are right. A missing file, a file that is not a JSON object,
a missing id or null are wrong.

The rules:

- ``number``: a JSON number, or a string that reads as one; equal in value.
- ``bool``: true or false, or the strings "true", "false", "yes", "no".
- ``name``: the name of a function or of an exception type. Compared after
  dropping spaces, backquotes and a trailing "()", and then only by its last
  dotted part: "builtins.KeyError" and "KeyError" are the same, and so are
  "GridEnv.step" and "step".
- ``file``: a file of the folder. Compared after dropping a leading "./"
  and the folder's own path.
- ``text``: compared as text, after dropping spaces around it; 200 and
  "200" are the same.
- ``{"set": rule}``: a list, in any order; the same items, each once.
- ``{"list": rule}``: a list, in order.
- ``{"record": {key: rule}}``: an object with these keys; other keys are
  not looked at.
- ``{"map": [key rule, rule]}``: an object whose keys are part of the
  answer: the same keys, and the same value under each.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))
MISSING = object()


def norm(rule, value, mount=""):
    """The value as the rule compares it, or MISSING when it is not one."""
    if rule == "number":
        if isinstance(value, bool):
            return MISSING
        if isinstance(value, str):
            try:
                value = float(value.strip())
            except ValueError:
                return MISSING
        return float(value) if isinstance(value, (int, float)) else MISSING
    if rule == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in ("true", "yes", "false", "no"):
            return value.strip().lower() in ("true", "yes")
        return MISSING
    if rule == "name":
        if not isinstance(value, str):
            return MISSING
        value = value.strip().strip("`").strip()
        if value.endswith("()"):
            value = value[:-2]
        return value.rsplit(".", 1)[-1]
    if rule == "file":
        if not isinstance(value, str):
            return MISSING
        value = value.strip().strip("`").strip()
        if mount and value.startswith(mount + "/"):
            value = value[len(mount) + 1:]
        while value.startswith("./"):
            value = value[2:]
        return value
    if rule == "text":
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            return MISSING
        return str(value).strip()
    raise ValueError(f"not a rule: {rule!r}")


def same(rule, given, oracle, mount=""):
    if isinstance(rule, str):
        mine = norm(rule, given, mount)
        return mine is not MISSING and mine == norm(rule, oracle, mount)
    (kind, inner), = rule.items()
    if kind == "list":
        return (isinstance(given, list) and len(given) == len(oracle)
                and all(same(inner, g, o, mount) for g, o in zip(given, oracle)))
    if kind == "set":
        if not isinstance(given, list) or len(given) != len(oracle):
            return False
        left = list(oracle)
        for item in given:
            match = next((n for n, o in enumerate(left) if same(inner, item, o, mount)), None)
            if match is None:
                return False
            del left[match]
        return True
    if kind == "record":
        return isinstance(given, dict) and all(
            key in given and same(inner[key], given[key], oracle[key], mount) for key in inner)
    if kind == "map":
        key_rule, value_rule = inner
        if not isinstance(given, dict) or len(given) != len(oracle):
            return False
        mine = {norm(key_rule, key, mount): value for key, value in given.items()}
        theirs = {norm(key_rule, key, mount): value for key, value in oracle.items()}
        return (len(mine) == len(given) and set(mine) == set(theirs)
                and all(same(value_rule, mine[key], theirs[key], mount) for key in theirs))
    raise ValueError(f"not a rule: {rule!r}")


def say(rule):
    """The format of an answer, as the question gives it to the agent."""
    if rule == "number":
        return "a number"
    if rule == "bool":
        return "true or false"
    if rule == "name":
        return "a name, as a string"
    if rule == "file":
        return "a file name, as a string"
    if rule == "text":
        return "a string"
    (kind, inner), = rule.items()
    if kind == "list":
        return f"a list, in order; each item: {say(inner)}"
    if kind == "set":
        return f"a list, in any order; each item: {say(inner)}"
    if kind == "record":
        return "an object with the keys " + ", ".join(f'"{k}" ({say(r)})' for k, r in inner.items())
    return f"an object with one key per item ({say(inner[0])}); under each key: {say(inner[1])}"


def grade(task, answers, oracle, mount=None):
    """(score, {id: right}) of one answers object. `oracle` is {id: answer}."""
    mount = f"/srv/{task}" if mount is None else mount
    right = {}
    for qid, rule in RULES[task].items():
        given = answers.get(qid) if isinstance(answers, dict) else None
        try:
            right[qid] = given is not None and bool(same(rule, given, oracle[qid], mount))
        except (TypeError, KeyError, AttributeError):
            right[qid] = False
    return sum(right.values()) / len(right), right


def read_answers(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv):
    task, path = argv[1], argv[2]
    oracle = json.loads((HERE / ".build" / "answers" / f"{task}.json").read_text(encoding="utf-8"))
    score, right = grade(task, read_answers(path), oracle)
    for qid, ok in right.items():
        print(f"{'right' if ok else 'wrong'}  {qid}")
    print(f"score {score:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
