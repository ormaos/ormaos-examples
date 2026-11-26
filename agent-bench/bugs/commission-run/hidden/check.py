"""The hidden check of commission-run.

Fixed means: a rep with deals in two product lines is paid each deal at the
rate of its product line. Still working means: a night on which every rep
sold in one product line gives the same payouts as before, with its shared
deal, its cancelled deal, its deal over 10,000.00 and its deal of somebody
who is not a rep.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)


def cases(name, code, scratch):
    before, yesterday = (
        (date.today() - timedelta(days=ago)).isoformat() for ago in (2, 1)
    )
    for case, rows in (
        ("reps sell in two product lines", scenario.LAST_NIGHT),
        ("every rep sells in one product line", scenario.QUIET_NIGHT),
    ):
        world = benchlib.check_world(name, code, scratch, case.replace(" ", "-"))
        done = scenario.play(world, last_night=rows)
        got = scenario.paid(world.folder)
        want = {before: scenario.expected(scenario.NIGHT_BEFORE_LAST), yesterday: scenario.expected(rows)}
        off = sorted(
            f"{rep} on {day}" for day in want for rep in want[day]
            if got.get(day, {}).get(rep) != want[day][rep]
        )
        passed = done.returncode == 0 and got == want
        yield case, passed, f"exit {done.returncode}, payouts not as expected: {off or 'none'}"


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
