"""The hidden check of points-grant.

Fixed means: a purchase with a member number changes the points of that
member only, also when another member has the same e-mail address. Still
working means: a night without such purchases gives the same points as
before, with its rows from the older tills (found by e-mail address), its
refunds, its purchase sent twice and its purchase under the minimum.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)


def cases(name, code, scratch):
    for case, rows in (
        ("members who share an address buy", scenario.LAST_NIGHT),
        ("nobody who shares an address buys", scenario.QUIET_NIGHT),
    ):
        world = benchlib.check_world(name, code, scratch, case.replace(" ", "-"))
        done = scenario.play(world, last_night=rows)
        points, grants = scenario.state(world.folder)
        want_points, want_grants = scenario.expected([scenario.NIGHT_BEFORE_LAST, rows])
        off = sorted(m for m in want_points if points.get(m) != want_points[m])
        passed = done.returncode == 0 and not off and grants == want_grants
        yield case, passed, (
            f"exit {done.returncode}, members with other points: {off or 'none'}, "
            f"grants {'as' if grants == want_grants else 'not as'} expected"
        )


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
