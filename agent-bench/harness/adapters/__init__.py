"""What the harness needs to know about one agent command line.

An adapter is one module in this folder, ``<name>.py`` with an ``ADAPTER``
(an instance of a subclass of ``Adapter``), and one container file next to
it, ``<name>.Containerfile``. Nothing else in the harness names an agent:
``load("claude-code")`` imports ``adapters.claude_code``.
"""

import importlib
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
KINDS = ("shell", "file")  # the tools every agent has, and no others
HOST = re.compile(r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?")


class Adapter:
    """One agent command line. A subclass sets every attribute and method."""

    name = None          # as in a run spec: "claude-code"
    cli_version = None   # the pinned version that the image layer installs
    build_args = {}      # passed to the container file, besides BASE
    hosts = ()           # the hosts the proxy lets this agent reach, on port 443; no wildcards
    probe = None         # a URL on the model's host: the canary must get an HTTP answer from it
    tools = {}           # the command line's name of every tool it is given -> "shell" or "file"
    efforts = ()         # the values of "effort" in a run spec, besides "default"
    env = {}             # the environment of the command line, besides HOME and the proxy
    renew = None         # the command that renews the credential on this machine, for the runner to print

    @property
    def containerfile(self):
        return HERE / f"{self.name.replace('-', '_')}.Containerfile"

    def home_files(self, source_home):
        """{path under ~: bytes}: the credential, and nothing else. The
        harness writes them, read-only, into the new home folder of a run."""
        raise NotImplementedError

    def secrets(self, source_home):
        """The strings of the credential that must not appear in a result."""
        raise NotImplementedError

    def credential_seconds(self, source_home):
        """How long the credential is still good for, read from the copy a
        run gets (``home_files``), or None when it does not say."""
        return None

    def argv(self, text, model, effort):
        """The command line for one task text. ``effort`` is "default" or
        one of ``efforts``."""
        raise NotImplementedError

    def parser(self):
        """A new object with ``feed(line) -> [event, ...]`` that turns the
        lines the command line prints into events of ``core/events.py``
        (without "v", "seq" and "t", which the harness adds)."""
        raise NotImplementedError


def check(adapter):
    """An adapter that breaks a rule of the harness does not load."""
    problems = []
    if not (adapter.name and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", adapter.name)):
        problems.append(f"name {adapter.name!r}")
    if not adapter.cli_version:
        problems.append("no pinned cli_version")
    if not adapter.hosts:
        problems.append("no hosts")
    for host in adapter.hosts:
        if not HOST.fullmatch(host):
            problems.append(f"host {host!r} is not a plain host name (no wildcards)")
    for tool, kind in adapter.tools.items():
        if kind not in KINDS:
            problems.append(f"tool {tool!r} is of kind {kind!r}, not one of {KINDS}")
    if not adapter.tools:
        problems.append("no tools")
    if not adapter.probe or not any(adapter.probe.startswith(f"https://{host}/") for host in adapter.hosts):
        problems.append(f"probe {adapter.probe!r} is not an https URL on one of its hosts")
    if not adapter.containerfile.exists():
        problems.append(f"{adapter.containerfile.name} is missing")
    if problems:
        raise ValueError(f"adapter {adapter.name}: " + "; ".join(problems))
    return adapter


def load(name):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        raise ValueError(f"not the name of an agent: {name!r}")
    try:
        module = importlib.import_module(f"adapters.{name.replace('-', '_')}")
    except ModuleNotFoundError as error:
        raise ValueError(f"no adapter for {name!r} in {HERE}") from error
    return check(module.ADAPTER)
