"""The morning after a night run of order-sync that skipped orders.

The job and the story are those of ``scenarios/morning_after.py``: last
night some marketplace orders had a SKU in a bad format (lowercase or
padded), the job skipped them and printed "sync finished: OK". This morning
the sales system has only today's orders, and the warehouse's count is in
``data/count.csv``.
"""

import csv
import shutil
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import benchlib

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "order-sync"
NOT_COPIED = ("seed", "reset.sh", "data", ".venv", ".ormaos", "__pycache__")
story = benchlib.load(REPO / "scenarios" / "morning_after.py", "morning_after")

NAME = "order-sync"
SAYS = "sync finished: OK"
RUNS_WITH = "python3 job.py --source api"
SYMPTOM = (
    "Last night's order sync run said OK, but this morning the stock of some "
    "products is not what the warehouse counted (data/count.csv)."
)
JOB = ["job.py", "--source", "api"]
# Last night with every SKU as the inventory writes it.
WELL_FORMED = [(n, t, sku.strip().upper(), *rest) for n, t, sku, *rest in story.LAST_NIGHT]


def play(world, last_night=story.LAST_NIGHT):
    today = date.today()
    before = story.rows_of(story.NIGHT_BEFORE_LAST, today - timedelta(days=2))
    night = before[-story.SENT_AGAIN:] + story.rows_of(last_night, today - timedelta(days=1))
    morning = night[-1:] + story.rows_of(story.TODAY, today)

    world.data.mkdir(exist_ok=True)
    stock = world.data / "stock.csv"
    shutil.copy(SOURCE / "seed" / "stock.csv", stock)
    world.run(["inventory.py", "--db", "data/inventory.db", "--create-from", "data/stock.csv"])
    stock.unlink()

    story.write_sales_data(world.folder, before)
    world.cron(JOB, says=SAYS)
    story.write_sales_data(world.folder, night)
    done = world.cron(JOB, bad=True)
    story.write_sales_data(world.folder, morning)

    count = story.physical_count(SOURCE / "seed" / "stock.csv", [before, night])
    with open(world.data / "count.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("sku", "counted"))
        writer.writerows(sorted(count.items()))
    world.clean()
    world.skipped = [row for row in night if row[2] != row[2].strip().upper()]
    return done


def stock(folder):
    conn = sqlite3.connect(folder / "data" / "inventory.db")
    rows = dict(conn.execute("SELECT sku, on_hand FROM stock"))
    conn.close()
    return rows


def counted(folder):
    with open(folder / "data" / "count.csv", newline="", encoding="utf-8") as handle:
        return {row["sku"]: int(row["counted"]) for row in csv.DictReader(handle)}


def data_left(folder):
    return sorted(stock(folder).items())


def wrong(folder):
    on_hand, count = stock(folder), counted(folder)
    return sorted(sku for sku in count if on_hand[sku] != count[sku])


def gone(world):
    """Last night's skipped orders: their numbers and their SKUs as sent."""
    return [row[0] for row in world.skipped] + [row[2] for row in world.skipped]


def wrong_after_today(folder):
    """After a run today: the stock against the count less today's orders."""
    today = date.today()
    before = story.rows_of(story.NIGHT_BEFORE_LAST, today - timedelta(days=2))
    night = before[-story.SENT_AGAIN:] + story.rows_of(story.LAST_NIGHT, today - timedelta(days=1))
    morning = night[-1:] + story.rows_of(story.TODAY, today)
    shelf = story.physical_count(SOURCE / "seed" / "stock.csv", [before, night, morning])
    on_hand = stock(folder)
    return sorted(sku for sku in shelf if on_hand[sku] != shelf[sku])
