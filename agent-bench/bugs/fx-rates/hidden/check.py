"""The hidden check of fx-rates.

Fixed means: a currency for which the feed answers 503 once gets its rate
from the next attempt. Still working means: a night without a busy feed
stores the same rates; a currency for which the feed stays busy keeps its
rate after a few attempts, not one and not endlessly, and so does a currency
the feed does not carry, while the job still ends OK.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)
STAYS_BUSY = 40


def differing(got, want):
    return sorted(c for c in want if got.get(c) != want[c])


def cases(name, code, scratch):
    for case, busy in (
        ("the feed is busy once for four currencies", scenario.BUSY_LAST_NIGHT),
        ("the feed is never busy", {}),
    ):
        world = benchlib.check_world(name, code, scratch, case.replace(" ", "-"))
        done = scenario.play(world, busy=busy)
        wrong = differing(scenario.stored(world.folder), scenario.expected())
        yield case, done.returncode == 0 and not wrong, f"exit {done.returncode}, not as expected: {wrong or 'none'}"

    case = "a currency stays busy and another is not carried"
    world = benchlib.check_world(name, code, scratch, "stays-busy")
    done = scenario.play(world, busy={"SEK": STAYS_BUSY}, without=("AUD",))
    wrong = differing(scenario.stored(world.folder), scenario.expected(stale=("SEK", "AUD")))
    state = json.loads((world.data / "feed.json").read_text(encoding="utf-8"))
    attempts = STAYS_BUSY - state["busy"].get("SEK", 0)
    passed = done.returncode == 0 and not wrong and 2 <= attempts <= 10
    yield case, passed, f"exit {done.returncode}, not as expected: {wrong or 'none'}, {attempts} attempts"


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
