"""The hidden check of order-sync.

Fixed means: a night with orders whose SKU is lowercase or padded does not
end as if nothing had happened. Either the stock is what the warehouse
counts (those orders were applied), or the job does not say OK (its exit
code is not 0, or it does not print "sync finished: OK"). Still working
means: the same night with well-formed SKUs ends OK with the stock the
warehouse counts: orders sent twice applied once, packs, back-orders.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)


def cases(name, code, scratch):
    world = benchlib.check_world(name, code, scratch, "bad-skus")
    done = scenario.play(world)
    off = scenario.wrong(world.folder)
    quiet = benchlib.said_ok(done, scenario.SAYS)
    yield (
        "orders with a SKU in a bad format", not off or not quiet,
        f"exit {done.returncode}, said OK: {quiet}, stock that is not the count: {off or 'none'}",
    )

    world = benchlib.check_world(name, code, scratch, "well-formed")
    done = scenario.play(world, last_night=scenario.WELL_FORMED)
    off = scenario.wrong(world.folder)
    quiet = benchlib.said_ok(done, scenario.SAYS)
    yield (
        "the same orders, well formed", quiet and not off,
        f"exit {done.returncode}, said OK: {quiet}, stock that is not the count: {off or 'none'}",
    )


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
