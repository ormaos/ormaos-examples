"""Build the morning after two night runs of the freight-quote job.

The story: freight-quote runs from cron at night. The warehouse system writes
a new dispatch list every evening, and the job replaces the quotes with the
quotes of that list. Cron keeps only what the job prints. This script plays
the warehouse system, the carrier and cron, and leaves the folder as it is
found in the morning:

1. the night before last: the carrier answers every call;
2. last night: the account's calls for the day are almost used up when the job
   starts, and the carrier refuses the rest with 429; the job prints
   "quotes finished: OK";
3. this morning: a new day at the carrier, the dispatch list is today's, and
   the bookings desk has put what the carrier charged for last night's
   shipments in ``data/booked.csv``.

The quotes of the night before last are then nowhere in the folder, and some
of last night's quotes are lower than what the carrier charged.

Usage::

    python3 scenarios/two_nights.py /tmp/freight-quote-morning
    python3 scenarios/two_nights.py /tmp/freight-quote-recorded --record

With ``--record`` the folder gets a ``.venv`` with Ormaos installed, the job
runs with ``.venv/bin/python``, and both nights are recorded with
``ormaos run``: the night before last is ``r1`` and last night is ``r2`` in
``.ormaos/`` in the folder. Without it, nothing is recorded.

The folder is the job as installed on a server: the code, the README, the
rate card and ``data/``. The try-out fixture (``seed/`` and ``reset.sh``) is
not copied.
"""

import argparse
import csv
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREIGHT_QUOTE = HERE.parent / "freight-quote"
ORMAOS_SOURCE = "git+https://github.com/ormaos/ormaos-python"
NOT_COPIED = ("seed", "reset.sh", "data", ".venv", ".ormaos", "__pycache__")
COLUMNS = ("shipment_id", "origin", "destination", "weight_kg",
           "length_cm", "width_cm", "height_cm", "service")
# How many of the account's calls for the day other systems had used when the
# job started. The account has 60 a day (seed/carrier.json).
USED_BEFORE = {"night before last": 12, "last night": 51, "this morning": 4}

# fmt: off
# (number, origin, destination, weight in kg, length, width, height in cm, service)
NIGHT_BEFORE_LAST = [
    (8101, 'STH', 'NTH', 75, 50, 40, 40, 'standard'),
    (8102, 'WST', 'NTH', 40, 30, 20, 10, 'standard'),
    (8103, 'NTH', 'STH', 2.4, 80, 60, 40, 'standard'),
    (8104, 'STH', 'NTH', 4, 50, 40, 40, 'standard'),
    (8105, 'WST', 'STH', 12, 120, 80, 60, 'standard'),
    (8106, 'STH', 'NTH', 4, 120, 80, 60, 'standard'),
    (8107, 'WST', 'NTH', 0.8, 35, 25, 15, 'standard'),
    (8108, 'NTH', 'EST', 1.5, 80, 60, 40, 'standard'),
    (8109, 'EST', 'STH', 1.5, 80, 60, 40, 'standard'),
    (8110, 'EST', 'WST', 4, 40, 30, 20, 'standard'),
    (8111, 'STH', 'NTH', 40, 40, 30, 20, 'standard'),
    (8112, 'STH', 'MID', 25, 80, 60, 40, 'express'),
    (8113, 'MID', 'EST', 6.5, 30, 20, 10, 'standard'),
    (8114, 'NTH', 'EST', 12, 50, 40, 40, 'standard'),
    (8115, 'NTH', 'NTH', 120, 30, 20, 10, 'express'),
    (8116, 'STH', 'EST', 40, 120, 80, 60, 'standard'),
    (8117, 'NTH', 'STH', 4, 80, 60, 40, 'standard'),
    (8118, 'MID', 'MID', 1.5, 30, 20, 10, 'express'),
    (8119, 'MID', 'EST', 9, 80, 60, 40, 'standard'),
    (8120, 'MID', 'EST', 9, 60, 40, 30, 'standard'),
    (8121, 'EST', 'STH', 0.8, 80, 60, 40, 'standard'),
    (8122, 'NTH', 'WST', 4, 120, 80, 60, 'standard'),
    (8123, 'NTH', 'MID', 2.4, 35, 25, 15, 'standard'),
    (8124, 'EST', 'EST', 0.8, 35, 25, 15, 'express'),
    (8125, 'STH', 'WST', 75, 60, 40, 30, 'express'),
    (8126, 'MID', 'WST', 18, 35, 25, 15, 'standard'),
]
LAST_NIGHT = [
    (8127, 'EST', 'EST', 4, 30, 20, 10, 'standard'),
    (8128, 'NTH', 'NTH', 0.8, 80, 60, 40, 'standard'),
    (8129, 'STH', 'STH', 120, 80, 60, 40, 'standard'),
    (8130, 'WST', 'MID', 6.5, 60, 40, 30, 'express'),
    (8131, 'NTH', 'NTH', 75, 60, 40, 30, 'express'),
    (8132, 'STH', 'MID', 6.5, 40, 30, 20, 'standard'),
    (8133, 'EST', 'MID', 1.5, 50, 40, 40, 'express'),
    (8134, 'NTH', 'STH', 120, 50, 40, 40, 'standard'),
    (8135, 'MID', 'NTH', 9, 80, 60, 40, 'standard'),
    (8136, 'MID', 'STH', 0.8, 50, 40, 40, 'standard'),
    (8137, 'STH', 'WST', 9, 120, 80, 60, 'express'),
    (8138, 'EST', 'MID', 18, 50, 40, 40, 'standard'),
    (8139, 'MID', 'EST', 120, 120, 80, 60, 'standard'),
    (8140, 'MID', 'MID', 6.5, 35, 25, 15, 'standard'),
    (8141, 'NTH', 'EST', 25, 30, 20, 10, 'express'),
    (8142, 'STH', 'NTH', 1.5, 50, 40, 40, 'standard'),
    (8143, 'NTH', 'WST', 75, 30, 20, 10, 'standard'),
    (8144, 'EST', 'NTH', 12, 80, 60, 40, 'express'),
    (8145, 'EST', 'WST', 18, 80, 60, 40, 'standard'),
    (8146, 'NTH', 'MID', 1.5, 50, 40, 40, 'standard'),
    (8147, 'WST', 'EST', 2.4, 120, 80, 60, 'standard'),
    (8148, 'STH', 'MID', 1.5, 60, 40, 30, 'standard'),
    (8149, 'MID', 'MID', 120, 30, 20, 10, 'standard'),
    (8150, 'EST', 'MID', 9, 60, 40, 30, 'standard'),
    (8151, 'STH', 'WST', 75, 40, 30, 20, 'standard'),
    (8152, 'STH', 'NTH', 40, 50, 40, 40, 'standard'),
]
TODAY = [
    (8153, 'NTH', 'MID', 9, 120, 80, 60, 'express'),
    (8154, 'MID', 'MID', 40, 30, 20, 10, 'express'),
    (8155, 'MID', 'EST', 120, 30, 20, 10, 'standard'),
    (8156, 'NTH', 'WST', 25, 40, 30, 20, 'express'),
    (8157, 'MID', 'STH', 75, 35, 25, 15, 'standard'),
    (8158, 'WST', 'NTH', 6.5, 35, 25, 15, 'express'),
    (8159, 'STH', 'STH', 12, 80, 60, 40, 'express'),
    (8160, 'STH', 'EST', 18, 50, 40, 40, 'standard'),
    (8161, 'STH', 'WST', 2.4, 120, 80, 60, 'standard'),
    (8162, 'MID', 'STH', 12, 120, 80, 60, 'express'),
]
# fmt: on


def rows_of(batch):
    return [(f"FR-{number}", *rest) for number, *rest in batch]


def write_dispatch_list(target, rows):
    with open(target / "data" / "shipments.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def set_calls_used(target, used):
    """The carrier's side: what the account has used of its day."""
    path = target / "data" / "carrier.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    state["calls_used_today"] = used
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def cron_run(target, command):
    """One run from cron: only what the job prints is kept."""
    done = subprocess.run(
        command, cwd=target, capture_output=True, text=True, check=False
    )
    stamp = datetime.now().isoformat(timespec="seconds")
    with open(target / "data" / "cron.log", "a", encoding="utf-8") as log:
        log.write(f"{stamp} freight-quote exit={done.returncode} {done.stdout.strip()}\n")
    if done.returncode != 0 or done.stdout != "quotes finished: OK\n":
        raise SystemExit(f"the job did not finish OK:\n{done.stdout}{done.stderr}")


def install_ormaos(target, source):
    venv = target / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    pip = [str(venv / "bin" / "python"), "-m", "pip", "install", "--quiet"]
    subprocess.run([*pip, source], check=True)


def module(folder, name):
    spec = importlib.util.spec_from_file_location(name, folder / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def charged_by_the_carrier(source, tariff, rows):
    """What the carrier charges when a shipment is booked: its tariff."""
    shipments, carrier = module(source, "shipments"), module(source, "carrier")
    charged = []
    for row in rows:
        shipment = shipments.parse_row(dict(zip(COLUMNS, map(str, row))))
        cents = carrier.tariff_price(
            tariff, shipment.lane, shipment.chargeable_kg, shipment.service
        )
        charged.append((shipment.shipment_id, cents))
    return charged


def check_nothing_is_left(target, rows):
    """The shipments of the night before last must be nowhere in the folder."""
    needles = [shipment_id.encode() for shipment_id, *_ in rows]
    for path in target.rglob("*"):
        if ".venv" in path.parts or not path.is_file():
            continue
        content = path.read_bytes()
        for needle in needles:
            if needle in content:
                raise SystemExit(f"{needle!r} is still in {path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", type=Path, help="the folder to create")
    parser.add_argument(
        "--record",
        action="store_true",
        help="install Ormaos in the folder and record both nights",
    )
    parser.add_argument(
        "--ormaos",
        default=ORMAOS_SOURCE,
        metavar="SOURCE",
        help="what pip installs with --record (a checkout path, or the default: "
        f"{ORMAOS_SOURCE})",
    )
    parser.add_argument(
        "--from", dest="source", type=Path, default=FREIGHT_QUOTE, help="freight-quote"
    )
    args = parser.parse_args(argv)
    target = args.target.resolve()
    if target.exists():
        parser.error(f"{target} already exists")

    shutil.copytree(args.source, target, ignore=shutil.ignore_patterns(*NOT_COPIED))
    (target / "data").mkdir()
    shutil.copy(args.source / "seed" / "carrier.json", target / "data" / "carrier.json")
    python = sys.executable
    job = [python, "job.py"]
    if args.record:
        install_ormaos(target, args.ormaos)
        python = ".venv/bin/python"
        job = [".venv/bin/ormaos", "run", "--", python, "job.py"]
    subprocess.run(
        [python, "quotes.py", "--db", "data/quotes.db", "--create"], cwd=target, check=True
    )

    before, last_night = rows_of(NIGHT_BEFORE_LAST), rows_of(LAST_NIGHT)
    for night, rows in (("night before last", before), ("last night", last_night)):
        write_dispatch_list(target, rows)
        set_calls_used(target, USED_BEFORE[night])
        cron_run(target, job)
    write_dispatch_list(target, rows_of(TODAY))
    state = set_calls_used(target, USED_BEFORE["this morning"])

    charged = charged_by_the_carrier(args.source, state["tariff"], last_night)
    with open(target / "data" / "booked.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("shipment_id", "charged_cents"))
        writer.writerows(charged)

    for cache in target.glob("__pycache__"):
        shutil.rmtree(cache)
    check_nothing_is_left(target, before)

    conn = sqlite3.connect(target / "data" / "quotes.db")
    quoted = dict(conn.execute("SELECT shipment_id, amount_cents FROM quotes"))
    conn.close()
    wrong = [shipment_id for shipment_id, cents in charged if quoted[shipment_id] != cents]
    print(f"morning after: {target}")
    print(f"last night: {len(last_night)} shipments quoted, "
          f"{len(wrong)} not at what the carrier charged")
    print(f"recorded: {'yes, both nights, in .ormaos/' if args.record else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
