"""The morning after a paused night of the late-fees job.

The billing system was under maintenance and the job ran with
``LATE_FEES_PAUSE=1``. When the maintenance ended, the switch was set to
``0`` in the job's environment instead of being removed. Last night the job
ran with ``LATE_FEES_PAUSE=0``, printed "late fees finished: OK" and charged
nothing. This morning the environment was cleaned up: the variable is gone.
"""

import sqlite3
from datetime import date, timedelta

NAME = "late-fees"
SAYS = "late fees finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's late-fees run said OK, but this morning the billing database "
    "has no late fee of last night for invoices that were overdue."
)
NIGHTS_BEFORE = (4, 3, 2)

# (invoice, customer, plan, cents, due days ago, paid days ago or None, disputed)
INVOICES = [
    ("INV-3101", "Alder Supply", "standard", 184000, 21, None, 0),
    ("INV-3102", "Birch & Co", "standard", 42000, 12, None, 0),
    ("INV-3103", "Cedar Works", "business", 960000, 30, None, 0),
    ("INV-3104", "Dune Retail", "standard", 600, 15, None, 0),
    ("INV-3105", "Elm Trading", "standard", 73500, 9, 3, 0),
    ("INV-3106", "Fern Logistics", "business", 250000, 16, None, 0),
    ("INV-3107", "Gale Foods", "standard", 128000, 8, None, 1),
    ("INV-3108", "Heath Print", "standard", 31000, 6, None, 0),
    ("INV-3109", "Iris Studio", "standard", 9900, 5, None, 0),
    ("INV-3110", "Juniper Labs", "business", 410000, 13, None, 0),
    ("INV-3111", "Kelp Marine", "standard", 56000, 4, None, 0),
    ("INV-3112", "Larch Homes", "standard", 220000, 2, None, 0),
    ("INV-3113", "Moss Garden", "standard", 15000, 40, 20, 0),
    ("INV-3114", "Nettle Tea", "standard", 87000, 18, 1, 0),
    ("INV-3115", "Oak Furniture", "business", 132000, 45, None, 0),
    ("INV-3116", "Pine Outdoors", "standard", 64000, -3, None, 0),
]


def invoice_rows(today):
    rows = []
    for invoice, customer, plan, cents, due_ago, paid_ago, disputed in INVOICES:
        due = today - timedelta(days=due_ago)
        paid = (today - timedelta(days=paid_ago)).isoformat() if paid_ago else None
        rows.append((invoice, customer, plan, cents, due.isoformat(), paid, disputed))
    return rows


def seed(world, today):
    """The billing system's side: the invoices."""
    world.data.mkdir(exist_ok=True)
    world.run(["invoices.py", "--create"])
    conn = sqlite3.connect(world.data / "billing.db")
    with conn:
        conn.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)", invoice_rows(today))
    conn.close()


def play(world, last_night={"LATE_FEES_PAUSE": "0"}):
    today = date.today()
    seed(world, today)
    for ago in NIGHTS_BEFORE:
        night = today - timedelta(days=ago)
        world.cron(["job.py", "--date", night.isoformat()], says=SAYS)
    night = today - timedelta(days=1)
    done = world.cron(["job.py", "--date", night.isoformat()], env=last_night, bad=True, says=SAYS)
    world.clean()
    return done


def fees(folder):
    conn = sqlite3.connect(folder / "data" / "billing.db")
    rows = conn.execute(
        "SELECT invoice_id, charged_on, fee_cents FROM fees ORDER BY charged_on, invoice_id"
    ).fetchall()
    conn.close()
    return rows


def data_left(folder):
    return fees(folder)


def wrong(folder):
    """The symptom in the data left: nights with fees, and none last night."""
    last_night = (date.today() - timedelta(days=1)).isoformat()
    nights = {charged_on for _, charged_on, _ in fees(folder)}
    return [] if last_night in nights or not nights else [f"no fee on {last_night}"]
