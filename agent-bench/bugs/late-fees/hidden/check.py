"""The hidden check of late-fees.

Fixed means: a night that runs with ``LATE_FEES_PAUSE=0`` charges its fees.
Still working means: ``LATE_FEES_PAUSE=1`` pauses the night, a night without
the variable charges, and a night run twice is charged once.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)
GRACE = {"standard": 3, "business": 14}


def expected(today, nights_ago):
    """The fees the rules of the README give, night by night."""
    fees, so_far = [], {}
    for ago in nights_ago:
        night = today - timedelta(days=ago)
        for invoice, _, plan, cents, due, paid, disputed in scenario.invoice_rows(today):
            late = (night - date.fromisoformat(due)).days
            if late <= GRACE[plan] or disputed:
                continue
            if paid is not None and date.fromisoformat(paid) <= night:
                continue
            fee = max(25, cents * 5 // 10000)
            fee = max(0, min(fee, cents * 10 // 100 - so_far.get(invoice, 0)))
            if fee:
                so_far[invoice] = so_far.get(invoice, 0) + fee
                fees.append((invoice, night.isoformat(), fee))
    return sorted(fees, key=lambda fee: (fee[1], fee[0]))


def cases(name, code, scratch):
    today = date.today()
    all_nights = (*scenario.NIGHTS_BEFORE, 1)
    for case, env, nights in (
        ("the night ran with LATE_FEES_PAUSE=0", {"LATE_FEES_PAUSE": "0"}, all_nights),
        ("a night with LATE_FEES_PAUSE=1 is paused", {"LATE_FEES_PAUSE": "1"}, scenario.NIGHTS_BEFORE),
        ("a night without the variable is charged", None, all_nights),
    ):
        world = benchlib.check_world(name, code, scratch, case.replace(" ", "-"))
        try:
            scenario.play(world, last_night=env)
            last = (today - timedelta(days=1)).isoformat()
            again = world.run(["job.py", "--date", last], env=env)
        except SystemExit as exc:
            yield case, False, str(exc).splitlines()[0]
            continue
        got, want = scenario.fees(world.folder), expected(today, nights)
        passed = got == want and again.returncode == 0
        yield case, passed, f"{len(got)} fees, {len(want)} expected, run twice exit {again.returncode}"


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
