"""The morning after reps sold in more than one product line on one day.

A rep's rate depends on the product line. Last night's deals file had reps
with deals in two product lines. The job printed "commissions finished: OK"
and deleted the file. This morning the inbox is empty (the next file comes
tonight), and finance's own numbers for yesterday differ from the payouts of
those reps.
"""

import csv
import sqlite3
from datetime import date, timedelta

NAME = "commission-run"
SAYS = "commissions finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's commission run said OK, but this morning the payouts of some "
    "reps for yesterday are not what finance worked out (data/finance_check.csv)."
)
REPS = [
    ("R-11", "Alba Nunes"), ("R-12", "Bento Cruz"), ("R-13", "Clara Dias"),
    ("R-14", "Duarte Gil"), ("R-15", "Elsa Maia"), ("R-16", "Fábio Reis"),
    ("R-17", "Gabi Lopes"), ("R-18", "Hélio Pais"),
]
RATES = [
    ("*", "hardware", 200), ("*", "software", 600), ("*", "services", 400),
    ("R-12", "software", 800), ("R-15", "hardware", 250), ("R-17", "services", 500),
    ("R-13", "software", 650),
]
# (deal, rep or reps, product line, cents, status)
NIGHT_BEFORE_LAST = [
    ("D-5101", "R-11", "hardware", 480000, "won"),
    ("D-5102", "R-12", "software", 1250000, "won"),
    ("D-5103", "R-13", "software", 96000, "won"),
    ("D-5104", "R-14", "services", 310000, "won"),
    ("D-5105", "R-15", "hardware", 720000, "won"),
    ("D-5106", "R-11", "hardware", 152000, "cancelled"),
    ("D-5107", "R-16+R-18", "services", 640000, "won"),
    ("D-5108", "R-17", "services", 205000, "won"),
    ("D-5109", "R-12", "software", 88000, "won"),
    ("D-5110", "R-15", "hardware", 1500000, "won"),
    ("D-5111", "R-19", "hardware", 90000, "won"),
]
LAST_NIGHT = [
    ("D-5112", "R-11", "hardware", 365000, "won"),
    ("D-5113", "R-12", "hardware", 540000, "won"),
    ("D-5114", "R-13", "software", 1180000, "won"),
    ("D-5115", "R-12", "software", 230000, "won"),
    ("D-5116", "R-14", "services", 99000, "won"),
    ("D-5117", "R-15", "software", 410000, "won"),
    ("D-5118", "R-16", "services", 275000, "won"),
    ("D-5119", "R-15", "hardware", 860000, "won"),
    ("D-5120", "R-17+R-13", "services", 520000, "won"),
    ("D-5121", "R-18", "hardware", 134000, "won"),
    ("D-5122", "R-14", "services", 450000, "cancelled"),
    ("D-5123", "R-17", "hardware", 300000, "won"),
    ("D-5124", "R-11", "hardware", 1020000, "won"),
    ("D-5125", "R-16", "services", 61000, "won"),
]
# The same night with every rep in one product line only.
QUIET_NIGHT = [
    row for row in LAST_NIGHT if row[0] not in ("D-5113", "D-5117", "D-5120", "D-5123")
]


def drop(world, day, rows):
    """The CRM's export: one file in the inbox."""
    inbox = world.folder / "inbox"
    inbox.mkdir(exist_ok=True)
    lines = ["deal_id,rep,product_line,amount_cents,status"]
    lines += [",".join(map(str, row)) for row in rows]
    name = f"deals-{day.strftime('%Y%m%d')}.csv"
    (inbox / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def expected(rows):
    """By the rules of the README: rep -> (deals, commission in cents)."""
    reps = {rep for rep, _ in REPS}
    rate = {(rep, line): bp for rep, line, bp in RATES}
    totals = {}
    for _, sellers, line, cents, status in rows:
        sellers = sellers.split("+")
        if status != "won":
            continue
        for rep in sellers:
            if rep not in reps:
                continue
            bp = rate.get((rep, line), rate[("*", line)]) + (50 if cents > 1_000_000 else 0)
            count, paid = totals.get(rep, (0, 0))
            totals[rep] = (count + 1, paid + cents // len(sellers) * bp // 10000)
    return totals


def play(world, last_night=LAST_NIGHT):
    today = date.today()
    before, yesterday = today - timedelta(days=2), today - timedelta(days=1)
    world.data.mkdir(exist_ok=True)
    world.run(["payouts.py", "--create"])
    conn = sqlite3.connect(world.data / "commissions.db")
    with conn:
        conn.executemany("INSERT INTO reps VALUES (?, ?)", REPS)
        conn.executemany("INSERT INTO rate_table VALUES (?, ?, ?)", RATES)
    conn.close()
    drop(world, before, NIGHT_BEFORE_LAST)
    world.cron(["job.py", "--date", before.isoformat()], says=SAYS)
    drop(world, yesterday, last_night)
    done = world.cron(["job.py", "--date", yesterday.isoformat()], bad=True, says=SAYS)

    with open(world.data / "finance_check.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("day", "rep_id", "commission_cents"))
        for day, rows in ((before, NIGHT_BEFORE_LAST), (yesterday, last_night)):
            for rep, (_, cents) in sorted(expected(rows).items()):
                writer.writerow((day.isoformat(), rep, cents))
    world.clean()
    return done


def paid(folder):
    """day -> rep -> (deals, cents)."""
    conn = sqlite3.connect(folder / "data" / "commissions.db")
    days = {}
    for day, rep, deals, cents in conn.execute("SELECT * FROM payouts"):
        days.setdefault(day, {})[rep] = (deals, cents)
    conn.close()
    return days


def data_left(folder):
    return sorted((day, sorted(reps.items())) for day, reps in paid(folder).items())


def wrong(folder):
    if list((folder / "inbox").glob("*")):
        raise SystemExit("the inbox is not empty")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    got, want = paid(folder)[yesterday], expected(LAST_NIGHT)
    return sorted(rep for rep in want if got.get(rep) != want[rep])


def gone(world):
    """Last night's deals."""
    return [row[0] for row in LAST_NIGHT]
