"""The morning after the statement-import job booked a statement in two parts.

The bank made last night's statement in two runs and put an empty line
between the two parts. The job booked the first part, printed "statement
import finished: OK" and deleted the file. This morning the inbox is empty
(the next statement comes tonight), and the bank's closing balance of
yesterday, exported from online banking, is not the balance of the ledger.
"""

import csv
import sqlite3
from datetime import date, timedelta

NAME = "statement-import"
SAYS = "statement import finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's statement import said OK, but this morning the balance of the "
    "ledger is not the bank's closing balance of yesterday (data/bank_balance.csv)."
)
ACCOUNT = "ACC-7701"
OPENING_CENTS = 1250000

# (bank id, amount, status, text), or (bank id, "R", the id it reverses)
NIGHT_BEFORE_LAST = [
    ("B-88101", "4200.00", "B", "Invoice 4391 Cedar Works"),
    ("B-88102", "312.40-", "B", "Card 4471 fuel"),
    ("B-88103", "1899.00-", "B", "Rent warehouse 2"),
    ("B-88104", "760.50", "B", "Invoice 4388 Heath Print"),
    ("B-88105", "58.90-", "B", "Card 4471 parking"),
    ("B-88106", "2400.00", "P", "Invoice 4395 Juniper Labs"),
    ("B-88107", "129.00-", "B", "Software subscription"),
    ("B-88108", "640.00-", "B", "Payroll tax advance"),
    ("B-88109", "88.20-", "B", "Card 4480 supplies"),
    ("B-88110", "R", "B-88105"),
    ("B-88111", "1310.75", "B", "Invoice 4390 Kelp Marine"),
    ("B-88112", "45.00-", "B", "Bank fee"),
    ("B-88113", "975.00", "B", "Invoice 4393 Moss Garden"),
    ("B-88114", "230.10-", "B", "Card 4480 courier"),
]
LAST_NIGHT_FIRST_PART = [
    ("B-88115", "510.00", "B", "Invoice 4396 Iris Studio"),
    ("B-88116", "74.30-", "B", "Card 4471 fuel"),
    ("B-88106", "2400.00", "B", "Invoice 4395 Juniper Labs"),
    ("B-88117", "1420.00-", "B", "Supplier Alder Supply"),
    ("B-88118", "66.00-", "B", "Card 4480 supplies"),
    ("B-88119", "3150.00", "B", "Invoice 4397 Fern Logistics"),
    ("B-88120", "18.50-", "B", "Card 4471 toll"),
    ("B-88121", "905.25", "P", "Invoice 4399 Larch Homes"),
    ("B-88122", "389.90-", "B", "Insurance"),
]
LAST_NIGHT_SECOND_PART = [
    ("B-88123", "2780.00", "B", "Invoice 4398 Oak Furniture"),
    ("B-88124", "R", "B-88118"),
    ("B-88125", "1260.40-", "B", "Supplier Birch & Co"),
    ("B-88126", "95.00-", "B", "Card 4480 courier"),
    ("B-88127", "430.00", "B", "Invoice 4400 Nettle Tea"),
    ("B-88128", "2105.00-", "B", "Payroll"),
    ("B-88129", "15.90-", "B", "Bank fee"),
    ("B-88130", "688.80", "B", "Invoice 4401 Dune Retail"),
    ("B-88131", "R", "B-88109"),
    ("B-88132", "349.00-", "B", "Card 4471 workshop"),
]
SENT_AGAIN = 2


def lines_of(records, day):
    lines = []
    for record in records:
        if record[1] == "R":
            lines.append(f"R|{record[0]}|{day}|{record[2]}")
        else:
            bank_id, amount, status, text = record
            lines.append(f"T|{bank_id}|{day}|{amount}|{status}|{text}")
    return lines


def statement_text(day, parts, between="\n\n", end="\n"):
    """A statement file: the header, then the parts with ``between`` between them."""
    bodies = ["\n".join(lines_of(part, day)) for part in parts]
    return f"H|{ACCOUNT}|{day}\n" + between.join(bodies) + end


def drop(world, day, text):
    """The bank's transfer: one file in the inbox."""
    inbox = world.folder / "inbox"
    inbox.mkdir(exist_ok=True)
    name = f"statement-{day.strftime('%Y%m%d')}.txt"
    (inbox / name).write_text(text, encoding="utf-8")


def last_night_parts():
    return [NIGHT_BEFORE_LAST[-SENT_AGAIN:] + LAST_NIGHT_FIRST_PART, LAST_NIGHT_SECOND_PART]


def play(world, last_night=None):
    """``last_night`` is the text of last night's file, given its date."""
    today = date.today()
    before, yesterday = today - timedelta(days=2), today - timedelta(days=1)
    world.data.mkdir(exist_ok=True)
    world.run(["ledger.py", "--create", str(OPENING_CENTS)])
    drop(world, before, statement_text(before, [NIGHT_BEFORE_LAST]))
    world.cron(["job.py"], says=SAYS)
    text = statement_text(yesterday, last_night_parts()) if last_night is None else last_night(yesterday)
    drop(world, yesterday, text)
    done = world.cron(["job.py"], bad=True, says=SAYS if last_night is None else None)

    with open(world.data / "bank_balance.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("date", "closing_cents"))
        writer.writerow((before.isoformat(), closing([NIGHT_BEFORE_LAST])))
        writer.writerow((yesterday.isoformat(), closing([NIGHT_BEFORE_LAST, *last_night_parts()])))
    world.clean()
    return done


def cents(amount):
    value = round(float(amount.rstrip("-")) * 100)
    return -value if amount.endswith("-") else value


def booked(batches):
    """What the bank booked: id -> cents, by the rules of the statement format."""
    entries = {"OPENING": OPENING_CENTS}
    for batch in batches:
        for record in batch:
            if record[0] in entries:
                continue
            if record[1] == "R":
                if record[2] in entries:
                    entries[record[0]] = -entries[record[2]]
            elif record[2] == "B":
                entries[record[0]] = cents(record[1])
    return entries


def closing(batches):
    return sum(booked(batches).values())


def entries(folder):
    conn = sqlite3.connect(folder / "data" / "ledger.db")
    rows = dict(conn.execute("SELECT bank_id, amount_cents FROM entries"))
    conn.close()
    return rows


def data_left(folder):
    return sorted(entries(folder).items())


def wrong(folder):
    ledger = sum(entries(folder).values())
    bank = closing([NIGHT_BEFORE_LAST, *last_night_parts()])
    left = list((folder / "inbox").glob("*"))
    if left:
        raise SystemExit(f"the inbox is not empty: {left}")
    return [] if ledger == bank else [f"ledger {ledger}, bank {bank}"]


def gone(world):
    """The second part of last night's statement."""
    return [record[0] for record in LAST_NIGHT_SECOND_PART]
