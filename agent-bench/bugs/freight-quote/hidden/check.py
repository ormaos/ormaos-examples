"""The hidden check of freight-quote.

Fixed means: a night on which the carrier refuses calls does not end as if
every quote were the carrier's. Either every quote is what the carrier
charges, or the job does not say OK (its exit code is not 0, or it does not
print "quotes finished: OK"). Still working means: a night on which the
carrier answers every call ends OK with every shipment quoted at the
carrier's price.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)


def cases(name, code, scratch):
    for case, used, must_say_ok in (
        ("the carrier refuses calls", scenario.USED["last night"], False),
        ("the carrier answers every call", scenario.USED["night before last"], True),
    ):
        world = benchlib.check_world(name, code, scratch, case.replace(" ", "-"))
        done = scenario.play(world, used_last_night=used)
        off = scenario.wrong(world.folder, world.quoted_last_night)
        quiet = benchlib.said_ok(done, scenario.SAYS)
        passed = (quiet and not off) if must_say_ok else (not off or not quiet)
        yield case, passed, (
            f"exit {done.returncode}, said OK: {quiet}, "
            f"{len(off)} shipments not quoted at the carrier's price"
        )


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
