"""The hidden check of statement-import.

Fixed means: a statement with an empty line between its two parts is booked
whole. Still working means: a statement in one part is booked as before, so
is one with empty lines and a comment at its end, and a statement of another
account is refused and left in the inbox.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)
PARTS = scenario.last_night_parts()
ALL = scenario.booked([scenario.NIGHT_BEFORE_LAST, *PARTS])


def cases(name, code, scratch):
    texts = {
        "a statement in two parts": lambda day: scenario.statement_text(day, PARTS),
        "a statement in one part": lambda day: scenario.statement_text(day, PARTS, between="\n"),
        "empty lines and a comment at the end": lambda day: scenario.statement_text(
            day, PARTS, between="\n# second run\n", end="\n\n# end of statement\n\n"
        ),
    }
    for case, text in texts.items():
        world = benchlib.check_world(name, code, scratch, case.replace(" ", "-"))
        done = scenario.play(world, last_night=text)
        got = scenario.entries(world.folder)
        left = list((world.folder / "inbox").glob("*"))
        passed = done.returncode == 0 and got == ALL and not left
        missing = len(set(ALL) - set(got))
        yield case, passed, f"exit {done.returncode}, {missing} of {len(ALL)} entries missing"

    case = "a statement of another account is refused"
    world = benchlib.check_world(name, code, scratch, "another-account")
    other = lambda day: scenario.statement_text(day, PARTS).replace(scenario.ACCOUNT, "ACC-9999")
    done = scenario.play(world, last_night=other)
    got = scenario.entries(world.folder)
    left = list((world.folder / "inbox").glob("*"))
    passed = done.returncode != 0 and got == scenario.booked([scenario.NIGHT_BEFORE_LAST]) and len(left) == 1
    yield case, passed, f"exit {done.returncode}, {len(left)} file left in the inbox"


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
