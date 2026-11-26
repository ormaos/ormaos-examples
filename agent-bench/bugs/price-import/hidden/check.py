"""The hidden check of price-import.

Fixed means: when the converter fails, the job does not say OK over a list
it took over in part. For the list of last night (one price is ``on
request``) the job either ends with an exit code that is not 0, or takes over
every row that has a price. For a list the converter cannot read at all (no
``price`` column) the job ends with an exit code that is not 0 and the
catalog stays as it was. Still working means: a list of prices only is taken
over as before, with its pack sizes, its article no longer sold, its new
article and its row in another currency.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import benchlib  # noqa: E402

scenario = benchlib.scenario(HERE.parent.name)


def differing(got, want):
    return sorted(sku for sku in set(want) | set(got) if got.get(sku) != want.get(sku))


def cases(name, code, scratch):
    case = "a list with a price that is not a number"
    world = benchlib.check_world(name, code, scratch, "not-a-number")
    done = scenario.play(world, last_night=scenario.list_text(2, not_a_number=True), corrected=False)
    wrong = differing(scenario.catalog(world.folder), scenario.expected(2, without=(scenario.NOT_A_NUMBER,)))
    passed = done.returncode != 0 or not wrong
    yield case, passed, f"exit {done.returncode}, {len(wrong)} products not at the list's price"

    case = "a list of prices only"
    world = benchlib.check_world(name, code, scratch, "prices-only")
    done = scenario.play(world, last_night=scenario.list_text(2), corrected=False)
    wrong = differing(scenario.catalog(world.folder), scenario.expected(2))
    yield case, done.returncode == 0 and not wrong, f"exit {done.returncode}, not as expected: {wrong or 'none'}"

    case = "a list without the price column"
    world = benchlib.check_world(name, code, scratch, "no-price-column")
    header = scenario.HEADER.replace("price", "amount")
    done = scenario.play(world, last_night=scenario.list_text(2, header=header), corrected=False)
    wrong = differing(scenario.catalog(world.folder), scenario.expected(1))
    yield case, done.returncode != 0 and not wrong, f"exit {done.returncode}, catalog changed: {wrong or 'no'}"


if __name__ == "__main__":
    sys.exit(benchlib.check_main(cases))
