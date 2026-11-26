"""What build.py, run.py and the hidden checks share: the sandbox and the
folder a job runs in.

Every run of a job, and every agent, is inside bubblewrap. The job's folder
is mounted at ``/srv/<name>``, the same path in every run, so the paths in a
trace or a recording are the paths the agent sees. Apart from that folder the
sandbox has the system (``/usr`` and ``/etc``, read-only) and an empty home
and ``/tmp``.
"""

import importlib.util
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUGS = ROOT / "bugs"
TOOLS = ROOT / ".build"
ARMS = ("none", "raw", "ormaos")
# Not part of the code of a job: its data and what an arm adds.
NOT_CODE = ("data", "inbox", ".venv", ".ormaos", "result.json", "__pycache__", "TASK.md")
VIZTRACER = "/opt/viztracer"
HOME = Path.home()


def bug_names():
    return sorted(p.parent.name for p in BUGS.glob("*/scenario.py"))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def scenario(name):
    return load(BUGS / name / "scenario.py", f"scenario_{name.replace('-', '_')}")


def mount_of(name):
    return f"/srv/{name}"


def sandbox(folder, mount, *, readonly=(), network=False, claude=False, env=None):
    """The bubblewrap command line in front of a command.

    ``readonly`` is a list of (host path, path inside). With ``claude`` the
    claude program and its login file are inside too, read-only.
    """
    argv = [
        "bwrap",
        "--ro-bind", "/usr", "/usr",
        "--symlink", "usr/bin", "/bin", "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/sbin", "/sbin",
        "--ro-bind", "/etc", "/etc",
        "--ro-bind-try", "/run/systemd/resolve", "/run/systemd/resolve",
        "--proc", "/proc", "--dev", "/dev",
        "--tmpfs", "/tmp", "--tmpfs", "/run/user", "--tmpfs", "/var",
        "--tmpfs", str(HOME),
    ]
    if claude:
        versions = HOME / ".local/share/claude/versions"
        login = HOME / ".claude/.credentials.json"
        argv += ["--ro-bind", str(versions), str(versions)]
        argv += ["--ro-bind", str(login), str(login)]
    for source, inside in readonly:
        argv += ["--ro-bind", str(source), str(inside)]
    argv += ["--bind", str(folder), mount, "--chdir", mount]
    argv += ["--unshare-pid", "--unshare-ipc", "--unshare-uts", "--die-with-parent"]
    if not network:
        argv += ["--unshare-net"]
    argv += ["--clearenv", "--setenv", "HOME", str(HOME), "--setenv", "LANG", "C.UTF-8"]
    argv += ["--setenv", "PATH", "/usr/local/bin:/usr/bin:/bin"]
    for key, value in (env or {}).items():
        argv += ["--setenv", key, str(value)]
    return argv


class World:
    """The folder of one job, and the cron that runs it.

    ``bad_run`` is what is put in front of the job for the one run that an
    arm keeps (a tracer or a recorder); every other run is ``python3``.
    """

    PLAIN = ("python3",)

    def __init__(self, name, folder, bad_run=PLAIN, readonly=()):
        self.name = name
        self.folder = Path(folder)
        self.mount = mount_of(name)
        self.bad_run = tuple(bad_run)
        self.readonly = tuple(readonly)

    @property
    def data(self):
        return self.folder / "data"

    def run(self, argv, env=None, bad=False, timeout=120):
        """Run the job in the sandbox, without the network."""
        front = self.bad_run if bad else self.PLAIN
        command = sandbox(self.folder, self.mount, readonly=self.readonly, env=env)
        return subprocess.run(
            [*command, *front, *argv],
            capture_output=True, text=True, check=False, timeout=timeout,
        )

    def cron(self, argv, env=None, bad=False, says=None):
        """One run from cron: only what the job prints is kept."""
        done = self.run(argv, env=env, bad=bad)
        printed = done.stdout.strip().splitlines()
        # A tracer prints its own lines around the job's.
        line = next((p for p in printed if says and p == says), " ".join(printed))
        stamp = datetime.now().isoformat(timespec="seconds")
        self.data.mkdir(exist_ok=True)
        with open(self.data / "cron.log", "a", encoding="utf-8") as log:
            log.write(f"{stamp} {self.name} exit={done.returncode} {line}\n")
        if says is not None and (done.returncode != 0 or says not in printed):
            raise SystemExit(
                f"{self.name}: the job did not finish with {says!r}:\n"
                f"{done.stdout}{done.stderr}"
            )
        return done

    def clean(self):
        for cache in self.folder.rglob("__pycache__"):
            shutil.rmtree(cache)


def copy_code(source, target):
    """The code of a job, without its data and without what an arm adds."""
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*NOT_CODE))


def check_world(name, code, scratch, case):
    """A fresh folder with the code under test, for one case of a check."""
    folder = Path(scratch) / case
    copy_code(code, folder)
    return World(name, folder)


def wilson(successes, total, z=1.959964):
    """The 95% Wilson score interval of a proportion."""
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    centre = p + z * z / (2 * total)
    spread = z * ((p * (1 - p) + z * z / (4 * total)) / total) ** 0.5
    low = (centre - spread) / (1 + z * z / total)
    high = (centre + spread) / (1 + z * z / total)
    return (max(0.0, low), min(1.0, high))


def check_main(cases, argv=None):
    """The command line of a hidden check: ``check.py <folder with the code>``.

    ``cases(name, code, scratch)`` yields (case, passed, detail). The check
    passes, with exit code 0, only when every case passes.
    """
    import tempfile

    argv = sys.argv if argv is None else argv
    code = Path(argv[1]).resolve()
    name = Path(sys.modules[cases.__module__].__file__).resolve().parents[1].name
    failed = 0
    with tempfile.TemporaryDirectory(prefix=f"check-{name}-") as scratch:
        for case, passed, detail in cases(name, code, Path(scratch)):
            failed += not passed
            print(f"{'pass' if passed else 'FAIL'}  {case}: {detail}")
    print("fixed" if not failed else "not fixed")
    return 0 if not failed else 1


def said_ok(done, says):
    """Whether a run ended the way cron reads as fine: exit 0 and the OK line."""
    return done.returncode == 0 and says in done.stdout.splitlines()


def assemble(name, arm, target):
    """The folder an agent gets: task/, and what the arm adds to it."""
    bug = BUGS / name
    shutil.copytree(bug / "task", target, symlinks=True)
    if arm == "raw":
        shutil.copy(bug / "arms" / "raw" / "result.json", target / "result.json")
    elif arm == "ormaos":
        for part in (".venv", ".ormaos"):
            shutil.copytree(bug / "arms" / "ormaos" / part, target / part, symlinks=True)
    return target


def prompt(name, arm):
    """The task: the same text in every arm, plus one sentence for the arm."""
    story = scenario(name)
    text = f"{story.SYMPTOM} The job runs from cron with `{story.RUNS_WITH}`. Find the cause and fix it."
    if arm == "raw":
        text += (
            " A VizTracer trace of that run is in result.json, in the Chrome Trace Event"
            ' format (JSON; "traceEvents" has one entry per function call, with its name,'
            ' its start "ts" and its duration "dur" in microseconds); read it with python3.'
        )
    elif arm == "ormaos":
        text += (
            " That run was recorded with Ormaos: the recording is in .ormaos/ and the"
            ' command line is .venv/bin/ormaos; run ".venv/bin/ormaos guide" first.'
        )
    return text
