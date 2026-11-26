"""The morning after the rate feed was busy for a moment.

Last night, while the fx-rates job ran, the feed answered 503 to the first
call for four currencies; a second call would have been answered. The job
printed "rates finished: OK". This morning the feed is not busy, and those
four currencies still have the rate of the day before.
"""

import json
import sqlite3
from datetime import date, timedelta
from decimal import Decimal

NAME = "fx-rates"
SAYS = "rates finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's rates run said OK, but this morning some currencies still have "
    "the rate published the day before, though the feed has a newer one."
)
BUSY_LAST_NIGHT = {"CHF": 1, "JPY": 1, "PLN": 1, "CAD": 1}
HELD = ("HUF",)  # moved more than 20% last night: held, by the rules

# currency: the rate three days ago, the night before last, last night
RATES = {
    "USD": ("1.0832", "1.0851", "1.0794"),
    "GBP": ("0.8571", "0.8566", "0.8590"),
    "CHF": ("0.9413", "0.9402", "0.9448"),
    "JPY": ("163.42", "163.90", "162.75"),
    "SEK": ("11.214", "11.230", "11.198"),
    "NOK": ("11.612", "11.598", "11.640"),
    "DKK": ("7.4592", "7.4590", "7.4594"),
    "PLN": ("4.3120", "4.3075", "4.3188"),
    "CZK": ("25.214", "25.240", "25.190"),
    "HUF": ("395.20", "396.10", "498.80"),
    "CAD": ("1.4718", "1.4730", "1.4682"),
    "AUD": ("1.6405", "1.6388", "1.6441"),
}


def micros(text):
    return int(Decimal(text) * 1_000_000)


def set_feed(world, published, column, busy=None, without=()):
    """The feed's side: what it publishes and for which currencies it is busy."""
    state = {
        "published": published.isoformat(),
        "rates": {c: r[column] for c, r in RATES.items() if c not in without},
        "busy": dict(busy or {}),
    }
    (world.data / "feed.json").write_text(json.dumps(state, indent=2), encoding="utf-8")


def play(world, busy=BUSY_LAST_NIGHT, without=()):
    today = date.today()
    days = [today - timedelta(days=ago) for ago in (3, 2, 1)]
    world.data.mkdir(exist_ok=True)
    world.run(["rates.py", "--create"])
    conn = sqlite3.connect(world.data / "rates.db")
    with conn:
        conn.executemany(
            "INSERT INTO rates VALUES (?, ?, ?)",
            [(c, micros(r[0]), days[0].isoformat()) for c, r in RATES.items()],
        )
    conn.close()
    set_feed(world, days[1], 1)
    world.cron(["job.py"], says=SAYS)
    set_feed(world, days[2], 2, busy=busy, without=without)
    done = world.cron(["job.py"], bad=True, says=SAYS)
    world.clean()
    return done


def stored(folder):
    conn = sqlite3.connect(folder / "data" / "rates.db")
    rows = {c: (m, p) for c, m, p in conn.execute("SELECT * FROM rates")}
    conn.close()
    return rows


def expected(stale=()):
    """Every rate is last night's, but the held ones and ``stale``."""
    today = date.today()
    before, last = (today - timedelta(days=ago) for ago in (2, 1))
    rows = {}
    for currency, rate in RATES.items():
        if currency in HELD or currency in stale:
            rows[currency] = (micros(rate[1]), before.isoformat())
        else:
            rows[currency] = (micros(rate[2]), last.isoformat())
    return rows


def data_left(folder):
    return sorted(stored(folder).items())


def wrong(folder):
    got, want = stored(folder), expected()
    return sorted(c for c in want if got[c] != want[c])
