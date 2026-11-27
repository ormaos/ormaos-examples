"""Run a batch: every task, arm and run of a spec, each once, each in a new
container.

Before the first run: the spec and its expectations are read, the task
folders are checked for agent configuration, the images are built, the
network is put up and the canary runs in it. Any of these can refuse the
batch, and then no run starts.

A run: the task folder is copied to ``work/<slot>`` and mounted at
``/srv/<task>``; a new home folder gets the agent's credential and nothing
else; the agent's command line gets the task text and the time limit. What
it prints goes to ``streams/`` as it is and to ``events/`` in the common
schema. The folder is graded outside the container by a process that is not
told who ran. The first attempt of every slot counts: nothing is run again,
nothing is left out.
"""

import importlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import adapters
from core import events, grading, report
from core import runtime as runtimes
from core import spec as specs
from core.spec import Refused

HARNESS = Path(__file__).resolve().parents[1]
# Files and folders that configure an agent. A task folder that holds one,
# at any depth, in any case, is refused.
AGENT_FILES = {
    "claude.md", "claude.local.md", "agents.md", "agents.override.md", "agent.md", "gemini.md", "grok.md",
    "codex.md", "copilot-instructions.md", "conventions.md", ".cursorrules", ".windsurfrules", ".clinerules",
    ".goosehints", ".mcp.json", "mcp.json", "opencode.json", "opencode.jsonc", ".aider.conf.yml",
    ".cursorignore", ".geminiignore", ".claudeignore", ".codexignore",
}
AGENT_FOLDERS = {
    ".claude", ".codex", ".gemini", ".grok", ".cursor", ".agents", ".agent", ".windsurf", ".cline", ".roo",
    ".opencode", ".continue", ".amazonq", ".kiro", ".qwen", ".aider", ".copilot", ".junie",
}
HOME_INSIDE = "/home/agent"
REDACTED = "[the credential, removed by the harness]"
HELLO = "Reply with the one word: ready"


def agent_config(folder):
    """The paths in a task folder that configure an agent."""
    found = []
    for path in sorted(Path(folder).rglob("*")):
        name = path.name.lower()
        if name in AGENT_FILES or (name in AGENT_FOLDERS and path.is_dir()) or name.startswith(".aider"):
            found.append(str(path.relative_to(folder)))
    return found


def new_home(adapter, source_home, parent):
    """A new home folder that holds the agent's credential, read-only, and
    nothing else."""
    home = Path(tempfile.mkdtemp(prefix="home-", dir=parent))
    for name, content in adapter.home_files(source_home).items():
        path = home / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o400)
    return home


def benchmark_of(name):
    if not name.isidentifier():
        raise Refused(f"not the name of a benchmark: {name!r}")
    try:
        return importlib.import_module(f"benchmarks.{name}")
    except ModuleNotFoundError as error:
        raise Refused(f"no benchmark {name!r} in the harness") from error


def plan_of(spec, benchmark):
    names = spec.get("tasks") or benchmark.tasks()
    for name in names:
        if name not in benchmark.tasks():
            raise Refused(f"{spec['benchmark']} has no task {name!r}")
    for arm in spec["arms"]:
        if arm not in benchmark.arms():
            raise Refused(f"{spec['benchmark']} has no arm {arm!r}")
    # Run by run, so that the arms of a task are spread over the time the whole takes.
    return [(name, arm, run) for run in range(1, spec["n"] + 1) for name in names for arm in spec["arms"]]


class Batch:
    def __init__(self, spec_path, *, runtime=None, root=HARNESS, source_home=None, out=None, jobs=1,
                 say=print, grader=grading.blind):
        self.root = Path(root)
        self.spec = specs.load(spec_path)
        self.spec_sha = specs.sha256(spec_path)
        self.expectations = specs.expectations(self.spec["name"], self.root)
        self.adapter = adapters.load(self.spec["agent"])
        if self.spec["effort"] != "default" and self.spec["effort"] not in self.adapter.efforts:
            raise Refused(f"{self.adapter.name} has no effort {self.spec['effort']!r}")
        self.benchmark = benchmark_of(self.spec["benchmark"])
        self.plan = plan_of(self.spec, self.benchmark)
        self.runtime = runtime
        self.source_home = Path(source_home or Path.home())
        self.jobs, self.say, self.grader = jobs, say, grader
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.out = Path(out) if out else (self.root / "results" / self.spec["benchmark"]
                                          / f"{self.adapter.name}-{self.spec['model']}" / stamp)
        self.network = f"ormaos-harness-{stamp}-{os.getpid()}"
        self.lock = threading.Lock()

    # before the first run

    def check_folders(self):
        problem = self.benchmark.not_built(sorted({name for name, _, _ in self.plan}))
        if problem:
            raise Refused(problem)
        for name, arm in sorted({(name, arm) for name, arm, _ in self.plan}):
            found = agent_config(self.benchmark.folder(name, arm))
            if found:
                raise Refused(f"the folder of {name}/{arm} holds agent configuration: {', '.join(found)}")

    def check_credential(self):
        left = self.adapter.credential_seconds(self.source_home)
        if left is not None and left < self.spec["time_limit_seconds"] + 120:
            raise Refused(f"the credential of {self.adapter.name} is good for {left:.0f} s more, less than one "
                          "run may take: log in again on this machine, then start the batch")

    def env(self, proxy):
        return {"HOME": HOME_INSIDE, "LANG": "C.UTF-8", "PATH": "/usr/local/bin:/usr/bin:/bin",
                **runtimes.proxy_env(proxy), **self.adapter.env}

    def canary(self, proxy, scratch, model=True):
        """The canary, in the image, on the network, with the environment
        and the home folder of a run. Returns (passed, what it printed)."""
        home = new_home(self.adapter, self.source_home, scratch)
        command = self.runtime.command(
            f"{self.network}-canary", self.images[1]["tag"], self.network, self.env(proxy),
            [(home, HOME_INSIDE, "rw")], "/tmp",
            ["harness-canary", self.adapter.probe, *self.adapter.home_files(self.source_home)])
        done = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
        said = (done.stdout + done.stderr).strip()
        lines = said.splitlines()
        passed = done.returncode == 0 and bool(lines) and all(line.startswith("PASS ") for line in lines)
        if passed and model:
            passed, line = self.hello(proxy, scratch)
            said += "\n" + line
        return passed, said

    def agent(self, container, command, secrets, stream, record, limit):
        """Run an agent's container to its end or to the time limit. What it
        prints goes to ``stream`` as it is (without the credential) and to
        ``record`` as events. Returns (exit code, whether the credential
        was printed)."""
        clock = time.monotonic()
        parser, timed_out, seen = self.adapter.parser(), threading.Event(), False

        def stop():
            timed_out.set()
            self.runtime.kill(container)

        with open(stream, "w", encoding="utf-8") as raw, open(record, "w", encoding="utf-8") as common:
            writer = events.Writer(common, lambda: time.monotonic() - clock)
            agent = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            timer = threading.Timer(limit, stop)
            timer.start()
            try:
                for line in agent.stdout:
                    for secret in secrets:
                        if secret in line:
                            seen, line = True, line.replace(secret, REDACTED)
                    raw.write(line)
                    raw.flush()
                    for event in parser.feed(line):
                        writer.add(event)
                code = agent.wait()
            finally:
                timer.cancel()
                agent.stdout.close()
            writer.close(time.monotonic() - clock, timed_out.is_set())
        return code, seen

    def hello(self, proxy, scratch):
        """The last line of the canary: the agent itself, with the model and
        the effort of the spec, answers one sentence through the proxy."""
        home = new_home(self.adapter, self.source_home, scratch)
        container = f"{self.network}-hello"
        command = self.runtime.command(
            container, self.images[1]["tag"], self.network, self.env(proxy), [(home, HOME_INSIDE, "rw")], "/tmp",
            self.adapter.argv(HELLO, self.spec["model"], self.spec["effort"]))
        stream, record = Path(scratch) / "hello.raw", Path(scratch) / "hello.jsonl"
        self.agent(container, command, self.adapter.secrets(self.source_home), stream, record, 180)
        facts = events.summary(events.read(record), self.adapter.tools)
        if facts["final"] == "done" and not facts["violations"]:
            return True, (f"PASS model: {self.adapter.name} {facts['cli_version']} answered as {facts['model']} "
                          f"through the proxy, with no tool beyond shell and files and no extension")
        why = "; ".join(facts["violations"]) or facts["error"] or stream.read_text(encoding="utf-8")[-300:]
        return False, f"FAIL model: {self.adapter.name} did not answer as planned: {why}"

    # one run

    def one(self, name, arm, run, proxy, scratch):
        slot = f"{name}-{arm}-{run}"
        work = self.out / "work" / slot
        stream, record = self.out / "streams" / f"{slot}.jsonl", self.out / "events" / f"{slot}.jsonl"
        shutil.copytree(self.benchmark.folder(name, arm), work, symlinks=True)
        home = new_home(self.adapter, self.source_home, scratch)
        secrets = self.adapter.secrets(self.source_home)
        mount = self.benchmark.mount(name)
        container = f"{self.network}-{slot}"
        command = self.runtime.command(
            container, self.images[1]["tag"], self.network, self.env(proxy),
            [(home, HOME_INSIDE, "rw"), (work, mount, "rw"), *self.benchmark.mounts(name, arm)], mount,
            self.adapter.argv(self.benchmark.text(name, arm), self.spec["model"], self.spec["effort"]))
        started = datetime.now().isoformat(timespec="seconds")
        code, seen = self.agent(container, command, secrets, stream, record, self.spec["time_limit_seconds"])
        shutil.rmtree(home, ignore_errors=True)

        facts = events.summary(events.read(record), self.adapter.tools)
        if seen:
            facts["violations"].append("the agent printed its credential; it was removed from the streams")
        for path in work.rglob("*"):  # and from the folder it left
            if path.is_file() and not path.is_symlink() and path.stat().st_size < 50_000_000:
                content = path.read_bytes()
                if any(secret.encode() in content for secret in secrets):
                    for secret in secrets:
                        content = content.replace(secret.encode(), REDACTED.encode())
                    path.write_bytes(content)
                    facts["violations"].append(f"the credential was in {path.relative_to(work)}; it was removed")
        graded = self.grader(self.spec["benchmark"], name, work, self.out / "oracle" / f"{name}.json")
        self.benchmark.tidy(work)
        return {
            "task": name, "arm": arm, "run": run, **graded, **facts,
            "agent": self.adapter.name, "effort": self.spec["effort"], "exit_code": code,
            "images": {"base": self.images[0]["id"], "agent": self.images[1]["id"]},
            "started": started,
            "stream": str(stream.relative_to(self.out)), "events": str(record.relative_to(self.out)),
            "folder": str(work.relative_to(self.out)),
        }

    # the batch

    def run(self):
        self.check_folders()
        self.check_credential()
        if (self.out / "results.jsonl").exists() or (self.out / "run.json").exists():
            raise Refused(f"{self.out} already has results: a slot is run once")
        self.runtime = self.runtime or runtimes.Runtime()
        self.images = self.runtime.images(self.adapter)
        python = self.runtime.do("run", "--rm", self.images[0]["tag"], "python3", "--version").stdout.split()[-1]
        if ".".join(python.split(".")[:2]) != self.benchmark.python():
            raise Refused(f"the image has Python {python}, the tasks were built with {self.benchmark.python()}")
        with tempfile.TemporaryDirectory(prefix="harness-") as scratch:
            try:
                proxy = self.runtime.network_up(self.network, self.adapter.hosts)
                passed, said = self.canary(proxy, scratch)
                self.say("canary:\n" + said)
                if not passed:
                    raise Refused("the canary failed: the batch does not start\n" + said)
                self.start(said, python)
                with open(self.out / "results.jsonl", "a", encoding="utf-8") as results:
                    def slot(name, arm, run):
                        record = self.one(name, arm, run, proxy, scratch)
                        with self.lock:
                            results.write(json.dumps(record) + "\n")
                            results.flush()
                            self.say(f"{name:14} {arm:14} run {run}: score {record['score']:.2f}, "
                                     f"{record['wall_seconds']:.0f} s, {record['tool_calls']} tool calls, "
                                     f"{record['final']}")
                    with ThreadPoolExecutor(max_workers=self.jobs) as pool:
                        for future in [pool.submit(slot, *each) for each in self.plan]:
                            future.result()
            finally:
                if (self.out / "run.json").exists():
                    (self.out / "proxy.jsonl").write_text(self.runtime.proxy_log(self.network), encoding="utf-8")
                self.runtime.network_down(self.network)
        self.finish()
        return self.out

    def start(self, canary, python):
        """Everything that is fixed when the first run starts."""
        for part in ("work", "streams", "events", "oracle"):
            (self.out / part).mkdir(parents=True)
        for name in sorted({name for name, _, _ in self.plan}):
            shutil.copy(self.benchmark.oracle(name), self.out / "oracle" / f"{name}.json")
        (self.out / "build.json").write_text(json.dumps(self.benchmark.manifest(), indent=2) + "\n")
        (self.out / "canary.txt").write_text(canary + "\n", encoding="utf-8")
        shutil.copy(self.expectations, self.out / "expectations.md")
        self.facts = {
            "spec": self.spec, "spec_sha256": self.spec_sha,
            "expectations": {"file": f"expectations/{self.spec['name']}.md",
                             "sha256": specs.sha256(self.expectations)},
            "agent": {"name": self.adapter.name, "cli_version": self.adapter.cli_version,
                      "hosts": list(self.adapter.hosts), "tools": self.adapter.tools,
                      "env": self.adapter.env, "home": sorted(self.adapter.home_files(self.source_home))},
            "images": {"base": self.images[0], "agent": self.images[1], "python": python},
            "runtime": self.runtime.do("--version").stdout.strip(),
            "jobs": self.jobs,
            "canary": canary.splitlines(),
            "plan": [list(slot) for slot in self.plan],
            "started": datetime.now().isoformat(timespec="seconds"),
            "finished": None,
        }
        (self.out / "run.json").write_text(json.dumps(self.facts, indent=2) + "\n", encoding="utf-8")

    def finish(self):
        self.facts["finished"] = datetime.now().isoformat(timespec="seconds")
        (self.out / "run.json").write_text(json.dumps(self.facts, indent=2) + "\n", encoding="utf-8")
        self.say("\n" + report.write(self.out, self.root))
