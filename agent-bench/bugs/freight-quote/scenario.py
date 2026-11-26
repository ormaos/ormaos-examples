"""The morning after a night on which the carrier refused calls.

The job and the story are those of ``scenarios/two_nights.py``: last night
the account's calls for the day were almost used up, the carrier refused the
rest with 429, and the job priced those shipments from the rate card and
printed "quotes finished: OK". This morning it is a new day at the carrier,
the dispatch list is today's, and what the carrier charged for last night's
shipments is in ``data/booked.csv``.
"""

import csv
import shutil
import sqlite3
from pathlib import Path

import benchlib

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "freight-quote"
NOT_COPIED = ("seed", "reset.sh", "data", ".venv", ".ormaos", "__pycache__")
story = benchlib.load(REPO / "scenarios" / "two_nights.py", "two_nights")

NAME = "freight-quote"
SAYS = "quotes finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's freight-quote run said OK, but this morning some of its quotes "
    "are lower than what the carrier charged (data/booked.csv)."
)
USED = story.USED_BEFORE


def play(world, used_last_night=USED["last night"]):
    before, night = story.rows_of(story.NIGHT_BEFORE_LAST), story.rows_of(story.LAST_NIGHT)
    world.data.mkdir(exist_ok=True)
    shutil.copy(SOURCE / "seed" / "carrier.json", world.data / "carrier.json")
    world.run(["quotes.py", "--db", "data/quotes.db", "--create"])

    story.write_dispatch_list(world.folder, before)
    story.set_calls_used(world.folder, USED["night before last"])
    world.cron(["job.py"], says=SAYS)
    story.write_dispatch_list(world.folder, night)
    story.set_calls_used(world.folder, used_last_night)
    done = world.cron(["job.py"], bad=True)
    world.quoted_last_night = quotes(world.folder)

    story.write_dispatch_list(world.folder, story.rows_of(story.TODAY))
    state = story.set_calls_used(world.folder, USED["this morning"])
    charged = story.charged_by_the_carrier(SOURCE, state["tariff"], night)
    with open(world.data / "booked.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("shipment_id", "charged_cents"))
        writer.writerows(charged)
    world.clean()
    world.before = before
    return done


def quotes(folder):
    conn = sqlite3.connect(folder / "data" / "quotes.db")
    rows = dict(conn.execute("SELECT shipment_id, amount_cents FROM quotes"))
    conn.close()
    return rows


def booked(folder):
    with open(folder / "data" / "booked.csv", newline="", encoding="utf-8") as handle:
        return {r["shipment_id"]: int(r["charged_cents"]) for r in csv.DictReader(handle)}


def data_left(folder):
    return sorted(quotes(folder).items())


def wrong(folder, quoted=None):
    quoted = quotes(folder) if quoted is None else quoted
    return sorted(s for s, cents in booked(folder).items() if quoted.get(s) != cents)


def gone(world):
    """The shipments of the night before last: each run replaces the quotes."""
    return [row[0] for row in world.before]


def wrong_after_today(folder):
    """A run today replaces the quotes: today's must all be the carrier's price."""
    import json

    state = json.loads((folder / "data" / "carrier.json").read_text(encoding="utf-8"))
    today = story.charged_by_the_carrier(SOURCE, state["tariff"], story.rows_of(story.TODAY))
    quoted = quotes(folder)
    return sorted(s for s, cents in today if quoted.get(s) != cents)
