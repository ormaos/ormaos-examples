"""What the tests share: an agent, a benchmark and a container program that
are not real, so that the rules of the runner can be tested without a model
and without containers."""

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS))

import adapters  # noqa: E402
from core import runtime as runtimes  # noqa: E402

AGENT = "zzagent"   # a name that must never reach the grader
MODEL = "zzmodel-9"
SECRET = "sk-zz-very-secret-token"
# HARNESS_NO_CONTAINERS=1 leaves out the tests that build images and start containers (CI sets it).
HAVE_RUNTIME = runtimes.find() is not None and not os.environ.get("HARNESS_NO_CONTAINERS")
PASSING = "PASS blocked: everything\nPASS reached: the model"
# What the agent that is not real does: it prints events, one per line, and
# writes its answers. argv: the task text.
SCRIPT = r'''
import json, os, sys, time
text = sys.argv[1]
def say(**event): print(json.dumps(event), flush=True)
say(type="start", agent="zzagent", cli_version="0.1", model="zzmodel-9", tools=json.loads(os.environ["FAKE_TOOLS"]), extensions=[])
if text.startswith("Reply"):
    say(type="final", text="ready", is_error=False, reason="done")
    sys.exit(0)
say(type="assistant_text", text="reading " + os.environ.get("FAKE_SAYS", ""))
say(type="tool_call", id="c1", tool="sh", kind="shell", input={"command": "ls"})
say(type="tool_result", id="c1", is_error=False, output="questions.json")
if "sleep" in text: time.sleep(30)
if "crash" in text: sys.exit(3)
json.dump({"q1": 1 if "right" in text else 2}, open("answers.json", "w"))
say(type="final", text="done", is_error=False, reason="done")
say(type="usage", input_tokens=10, output_tokens=5, cache_read_tokens=None, cache_write_tokens=None, cost_usd=None, turns=2)
'''


class Passthrough:
    def feed(self, line):
        try:
            event = json.loads(line)
        except ValueError:
            return []
        return [event] if isinstance(event, dict) and "type" in event else []


class FakeAdapter(adapters.Adapter):
    name = AGENT
    cli_version = "0.1"
    hosts = ("model.example.com",)
    probe = "https://model.example.com/"
    tools = {"sh": "shell", "edit": "file"}
    efforts = ("high",)
    env = {}
    containerfile = HARNESS / "image" / "Containerfile"
    renew = "zz login"
    lefts = ()  # what credential_seconds answers, call by call; after them, None

    def credential_seconds(self, source_home):
        self.lefts = list(self.lefts)
        return self.lefts.pop(0) if self.lefts else None

    def home_files(self, source_home):
        return {".zz/credential": SECRET.encode()}

    def secrets(self, source_home):
        return [SECRET]

    def argv(self, text, model, effort):
        return ["zz", text]

    def parser(self):
        return Passthrough()


class FakeRuntime:
    """Runs the 'container' as a process on this machine, in the folder
    mounted for writing under /srv."""

    program = "fake"

    def __init__(self, canary=PASSING, tools=("sh", "edit"), says=""):
        self.canary_says, self.tools, self.says = canary, list(tools), says
        self.commands, self.up, self.down = [], 0, 0

    def images(self, adapter, rebuild=False):
        return ({"tag": "base", "id": "sha256:base", "layers": ["a"]},
                {"tag": "agent", "id": "sha256:agent", "layers": ["a", "b"]})

    def do(self, *args, **options):
        return types.SimpleNamespace(stdout="Python 3.14.4\n" if "python3" in args else "fake 1.0\n", returncode=0)

    def network_up(self, name, allow):
        self.up += 1
        return "http://127.0.0.1:9"

    def network_down(self, name):
        self.down += 1

    def proxy_log(self, name):
        return json.dumps({"time": 1, "client": "x", "allowed": False, "method": "CONNECT",
                           "target": "github.com:443"}) + "\n"

    def kill(self, name):
        self.killed = name
        self.process_to_kill and self.process_to_kill()

    process_to_kill = None

    def command(self, name, image, network, env, mounts, workdir, argv):
        self.commands.append({"name": name, "env": env, "mounts": mounts, "workdir": workdir, "argv": argv})
        if argv[0] == "harness-canary":
            return [sys.executable, "-c", f"print({self.canary_says!r})"]
        work = next((str(source) for source, inside, mode in mounts if inside.startswith("/srv/")), None)
        code = ("import os,sys\n" + (f"os.chdir({work!r})\n" if work else "")
                + f"os.environ['FAKE_TOOLS']={json.dumps(json.dumps(self.tools))}\n"
                + f"os.environ['FAKE_SAYS']={self.says!r}\n" + SCRIPT.replace("sys.argv[1]", "sys.argv[1]"))
        return [sys.executable, "-c", code, argv[-1]]


def fake_benchmark(folder):
    """A benchmark of one task, t1, with arms whose names are in the text."""
    module = types.ModuleType("benchmarks.fakebench")
    module.NAME = "fakebench"
    module.tasks = lambda: ["t1"]
    module.arms = lambda: ["right", "wrong", "sleep", "crash"]
    module.text = lambda task, arm: f"Answer the question. ({arm})"
    module.mount = lambda task: f"/srv/{task}"
    module.manifest = lambda: {"tasks": {"t1": {}}, "python": "Python 3.14.4"}
    module.not_built = lambda names: None
    module.python = lambda: "3.14"
    module.folder = lambda task, arm: folder
    module.mounts = lambda task, arm: []
    module.oracle = lambda task: folder.parent / "oracle.json"
    module.tidy = lambda work: None
    return module


def fake_grader(benchmark, task, work, oracle_file):
    try:
        answers = json.loads((Path(work) / "answers.json").read_text())
    except (OSError, ValueError):
        answers = None
    right = {"q1": bool(answers) and answers.get("q1") == json.loads(Path(oracle_file).read_text())["q1"]}
    return {"score": float(right["q1"]), "right": right, "answers": answers,
            "answers_file": "read" if answers is not None else "missing or not JSON"}


class Sandbox(unittest.TestCase):
    """A harness root in a temporary folder, with the agent and the
    benchmark that are not real."""

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name) / "harness"
        for part in ("specs", "expectations", "results"):
            (self.root / part).mkdir(parents=True)
        self.task = Path(self.scratch.name) / "bench" / "t1"
        self.task.mkdir(parents=True)
        (self.task / "questions.json").write_text('{"questions": []}')
        (self.task.parent / "oracle.json").write_text('{"q1": 1}')
        self.home = Path(self.scratch.name) / "home"
        self.home.mkdir()
        adapter = types.ModuleType("adapters.zzagent")
        adapter.ADAPTER = FakeAdapter()
        self.modules = {"adapters.zzagent": adapter, "benchmarks.fakebench": fake_benchmark(self.task)}
        sys.modules.update(self.modules)
        self.addCleanup(lambda: [sys.modules.pop(name, None) for name in self.modules])

    def spec(self, name="try", expectations="What I expect.\n", **changes):
        fields = {"benchmark": "fakebench", "arms": ["right", "wrong"], "agent": AGENT, "model": MODEL,
                  "effort": "default", "n": 1, "time_limit_seconds": 20, **changes}
        path = self.root / "specs" / f"{name}.toml"
        path.write_text("\n".join(f"{key} = {json.dumps(value)}" for key, value in fields.items()) + "\n")
        if expectations is not None:
            (self.root / "expectations" / f"{name}.md").write_text(expectations)
        return path

    def batch(self, spec=None, runtime=None, **options):
        from core import runner

        self.runtime = runtime or FakeRuntime()
        return runner.Batch(spec or self.spec(), runtime=self.runtime, root=self.root, source_home=self.home,
                            say=lambda text: None, grader=options.pop("grader", fake_grader), **options)

    def results(self, out):
        return [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines()]
