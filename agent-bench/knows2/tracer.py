"""The oracle's tracer: the one of ``use-cases/common.py`` (``sys.settrace``,
a wrapper around ``open`` and one around ``sqlite3.connect``), extended with
what the questions of knows2 ask and that tracer does not keep.

    python tracer.py --trace out.json script.py [args...]

More than ``common.py``:

- values: every argument and result also as JSON (``"json"``), when it is
  small enough; a DataFrame with its rows, a tensor with its numbers;
- the lines every call ran (``"lines"``), not only those of chosen functions;
- the local variables of every call when it returned (``"locals"``), and
  those of the script itself (``"globals"``, of ``__main__``);
- the message of every exception (``"message"``), the call it was raised in
  and the call that handled it (``"raised_call"``, ``"handled_call"``);
- what the process wrote to its standard output and error.

It runs in the process of the program, without Ormaos, and reads no
recording and no trace of another tool.
"""

import argparse
import dataclasses
import json
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, "/opt/use-cases")
import common  # noqa: E402

LIMIT = 200_000  # characters of JSON kept for one value
base_describe = common.describe


def plain(value, depth=0):
    """The value as JSON can hold it."""
    kind = type(value)
    module = kind.__module__ or ""
    if value is None or kind in (bool, int, str):
        return value
    if kind is float:
        return value if value == value and value not in (float("inf"), float("-inf")) else repr(value)
    if depth > 8:
        return f"<{kind.__qualname__}>"
    if kind in (list, tuple):
        return [plain(item, depth + 1) for item in value]
    if kind in (set, frozenset):
        return sorted((plain(item, depth + 1) for item in value), key=repr)
    if isinstance(value, dict):
        return {str(key): plain(item, depth + 1) for key, item in value.items()}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {"__class__": kind.__qualname__,
                **{f.name: plain(getattr(value, f.name, None), depth + 1) for f in dataclasses.fields(value)}}
    if module.startswith("pandas") and kind.__name__ == "DataFrame":
        return {"__class__": "DataFrame", "columns": [str(c) for c in value.columns],
                "dtypes": {str(c): str(t) for c, t in value.dtypes.items()},
                "index": [plain(i, depth + 1) for i in value.index.tolist()],
                "rows": json.loads(value.to_json(orient="records", date_format="iso"))}
    if module.startswith("pandas") and kind.__name__ == "Series":
        return {"__class__": "Series", "name": plain(value.name, depth + 1),
                "index": [plain(i, depth + 1) for i in value.index.tolist()],
                "values": json.loads(value.to_json(orient="values", date_format="iso"))}
    if module.startswith("torch") and kind.__name__ in ("Tensor", "Parameter"):
        return {"__class__": "Tensor", "shape": [int(n) for n in value.shape], "dtype": str(value.dtype),
                "values": plain(value.detach().tolist(), depth + 1) if value.numel() <= 5000 else None}
    if module.startswith("numpy") and hasattr(value, "tolist"):
        return plain(value.tolist(), depth + 1)
    if kind.__name__ in ("date", "datetime", "Decimal", "PosixPath", "Path", "Timestamp"):
        return str(value)
    if isinstance(value, BaseException):
        return {"__class__": kind.__qualname__, "message": str(value)}
    if isinstance(value, (bytes, bytearray)):
        return {"__class__": kind.__name__, "len": len(value), "text": bytes(value[:2000]).decode("utf-8", "replace")}
    fields = getattr(value, "__dict__", None)
    if isinstance(fields, dict) and depth < 3 and not module.startswith(("torch", "pandas", "sqlite3", "http", "socket")):
        return {"__class__": kind.__qualname__,
                **{str(k): plain(v, depth + 2) for k, v in fields.items() if not str(k).startswith("__")}}
    return f"<{kind.__qualname__}>"


def describe(value):
    found = base_describe(value)
    try:
        text = json.dumps(plain(value))
        if len(text) <= LIMIT:
            found["json"] = json.loads(text)
    except Exception as error:  # a value that cannot be read is left without "json"
        found["json_error"] = type(error).__name__
    return found


common.describe = describe


class Everything:
    """Every function keeps its lines."""

    def __contains__(self, name):
        return True


class Tracer(common.Tracer):
    def __init__(self, root, is_program=None):
        super().__init__(root, (), is_program)
        self.line_functions = Everything()

    def local_trace(self, frame, event, arg):
        local = self.state()
        if not local.busy:
            record = local.stack[-1] if local.stack else None
            if event == "exception":
                known = len(self.exceptions)
                super().local_trace(frame, event, arg)
                if len(self.exceptions) > known:
                    self.exceptions[-1]["message"] = str(arg[1])
                    self.exceptions[-1]["raised_call"] = record["id"] if record else None
                return self.local_trace
            if event == "line":
                pending = local.pending.get(id(frame))
                if pending is not None:
                    pending["handled_call"] = record["id"] if record else None
            if event == "return" and record is not None:
                local.busy = True
                try:
                    kept = {}
                    for name, value in list(frame.f_locals.items()):
                        if name.startswith("__") or type(value).__name__ in ("module", "function", "type"):
                            continue
                        kept[name] = describe(value)
                    record["locals"] = kept
                    record["returned_at_line"] = frame.f_lineno
                finally:
                    local.busy = False
        return super().local_trace(frame, event, arg)


class Tee:
    def __init__(self, real, kept):
        self.real, self.kept = real, kept

    def write(self, text):
        self.kept.append(text)
        return self.real.write(text)

    def __getattr__(self, name):
        return getattr(self.real, name)


def kernel_tracer():
    """A tracer for a Jupyter kernel: the program is the code of the cells."""
    tracer = Tracer(Path.cwd().resolve(), is_program=common._is_cell)
    tracer.install()
    return tracer


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("script")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    import runpy

    root = Path.cwd().resolve()
    tracer = Tracer(root)
    sys.argv = [args.script, *args.rest]
    sys.path.insert(0, str(root))
    out, err = [], []
    sys.stdout, sys.stderr = Tee(sys.stdout, out), Tee(sys.stderr, err)
    tracer.install()
    code, script = 0, {}
    try:
        script = runpy.run_path(str(root / args.script), run_name="__main__")
    except SystemExit as stop:
        code = stop.code if isinstance(stop.code, int) else (0 if stop.code is None else 1)
    finally:
        found = tracer.result()
        sys.stdout, sys.stderr = sys.stdout.real, sys.stderr.real
        found["stdout"], found["stderr"], found["exit_code"] = "".join(out), "".join(err), code
        found["globals"] = {name: describe(value) for name, value in script.items()
                            if not name.startswith("__")
                            and type(value).__name__ not in ("module", "function", "type")}
        found["threads_at_end"] = threading.active_count()
        found["pid"] = os.getpid()
        args.trace.write_text(json.dumps(found), encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
