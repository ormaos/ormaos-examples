"""The harness: any coding agent command line, the same benchmark tasks,
the same conditions.

    python3 harness.py run specs/smoke.toml     # canary, then every run of the spec, then the report
    python3 harness.py run specs/smoke.toml --continue results/<benchmark>/<agent>-<model>/<time>
                                                # a batch that stopped: only the runs that never started
    python3 harness.py canary claude-code       # only the canary of an agent
    python3 harness.py images claude-code       # build the images again
    python3 harness.py report results/<benchmark>/<agent>-<model>/<time>
    python3 harness.py check                    # every results folder: expectations unchanged, events valid,
                                                # report.md what they say; writes nothing

See README.md.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
sys.path.insert(0, str(HARNESS))

import adapters  # noqa: E402
from core import report, runner, runtime as runtimes  # noqa: E402
from core.spec import Refused  # noqa: E402


def need_runtime():
    if runtimes.find() is None:
        sys.exit("Neither podman nor docker is installed. Install one, for example:\n"
                 "    sudo apt-get install -y podman")
    return runtimes.Runtime()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run a spec")
    run.add_argument("spec", type=Path)
    run.add_argument("--jobs", type=int, default=1, help="runs at the same time (default 1)")
    run.add_argument("--continue", dest="resume", type=Path, metavar="FOLDER",
                     help="the results folder of a batch that stopped: start only the runs that never started")
    for name in ("canary", "images"):
        commands.add_parser(name).add_argument("agent")
    commands.add_parser("report").add_argument("folder", type=Path)
    commands.add_parser("check")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            runner.Batch(args.spec, runtime=need_runtime(), jobs=args.jobs, resume=bool(args.resume),
                         out=args.resume.resolve() if args.resume else None).run()
        elif args.command == "images":
            base, agent = need_runtime().images(adapters.load(args.agent), rebuild=True)
            print(json.dumps({"base": base, "agent": agent}, indent=2))
        elif args.command == "canary":
            return canary(args.agent)
        elif args.command == "report":
            print(report.write(args.folder.resolve()))
        elif args.command == "check":
            folders = sorted(path.parent for path in (HARNESS / "results").glob("*/*/*/run.json"))
            for folder in folders:
                report.check(folder)
                print(f"ok  {folder.relative_to(HARNESS)}")
            print(f"{len(folders)} results folders")
    except (Refused, runtimes.RuntimeError_, ValueError) as error:
        sys.exit(f"refused: {error}")
    return 0


def canary(agent):
    """The canary of an agent, on a network of its own."""
    batch = runner.Batch.__new__(runner.Batch)
    batch.adapter, batch.runtime, batch.source_home = adapters.load(agent), need_runtime(), Path.home()
    batch.network = f"ormaos-harness-canary-{id(batch) % 100000}"
    batch.images = batch.runtime.images(batch.adapter)
    with tempfile.TemporaryDirectory(prefix="harness-") as scratch:
        try:
            passed, said = batch.canary(batch.runtime.network_up(batch.network, batch.adapter.hosts), scratch,
                                          model=False)
        finally:
            batch.runtime.network_down(batch.network)
    print(said)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
