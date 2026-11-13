"""Build the "morning after" state of the order-sync job in a new folder.

The story: order-sync runs from cron at night. It asks the sales system for
the new orders; the sales system hands every order over once and moves on.
Cron keeps only what the job prints. This script plays the sales system and
cron for three nights and leaves the folder as it is found in the morning:

1. the night before last: a batch of orders, all well formed;
2. last night: a batch in which some orders carry a SKU in a bad format
   (lowercase or padded); the job prints "sync finished: OK";
3. this morning: the sales system has only today's orders, all well formed,
   and the warehouse has put its physical count in ``data/count.csv``.

Last night's orders are then nowhere in the folder: not in the sales data,
not in a log. The inventory is wrong for the SKUs of the skipped orders.

Usage::

    python3 scenarios/morning_after.py /tmp/order-sync-morning
    python3 scenarios/morning_after.py /tmp/order-sync-morning --record

With ``--record`` the folder gets a ``.venv`` with Ormaos installed, the job
runs with ``.venv/bin/python``, and last night's run is recorded with
``ormaos run``: the recording is in ``.ormaos/`` in the folder. Without it,
nothing is recorded.

The folder is the job as installed on a server: the code, the README and
``data/``. The try-out fixture (``seed/`` and ``reset.sh``) is not copied.
"""

import argparse
import csv
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER_SYNC = HERE.parent / "order-sync"
ORMAOS_SOURCE = "git+https://github.com/ormaos/ormaos-python"
NOT_COPIED = ("seed", "reset.sh", "data", ".venv", ".ormaos", "__pycache__")
COLUMNS = ("order_id", "placed_at", "sku", "quantity", "channel", "unit")

# (number, time of day, SKU as the sales system sent it, quantity, channel, unit)
NIGHT_BEFORE_LAST = [
    (501, "08:12", "KBD-0101", 2, "web", "each"),
    (502, "08:40", "CAB-0302", 3, "store", "pack"),
    (503, "09:05", "DOC-0501", 6, "marketplace", "each"),
    (504, "09:51", "MSE-0102", 4, "web", "each"),
    (505, "10:30", "HDS-0402", 3, "store", "each"),
    (506, "11:02", "MON-0201", 2, "web", "each"),
    (507, "11:47", "DOC-0501", 8, "web", "each"),
    (508, "12:20", "HUB-0301", 5, "marketplace", "each"),
    (509, "13:15", "WEB-0401", 4, "store", "each"),
    (510, "14:08", "KBD-0101", 6, "marketplace", "each"),
    (511, "15:33", "MSE-0102", 2, "store", "pack"),
    (512, "16:10", "DOC-0501", 5, "marketplace", "each"),
    (513, "17:26", "HDS-0402", 4, "web", "each"),
    (514, "18:45", "CAB-0302", 12, "web", "each"),
]
LAST_NIGHT = [
    (515, "07:58", "MSE-0102", 3, "web", "each"),
    (516, "08:21", "KBD-0101", 4, "store", "each"),
    (517, "08:49", "DOC-0501", 4, "web", "each"),
    (518, "09:17", "CAB-0302", 2, "store", "pack"),
    (519, "09:40", "WEB-0401", 2, "web", "each"),
    (520, "10:03", "HUB-0301", 3, "store", "pack"),
    (521, "10:36", "kbd-0101", 3, "marketplace", "each"),
    (522, "11:01", "MON-0201", 2, "web", "each"),
    (523, "11:29", "HDS-0402", 1, "store", "pack"),
    (524, "12:05", "DOC-0501", 9, "marketplace", "each"),
    (525, "12:44", "MSE-0102", 6, "store", "each"),
    (526, "13:10", "KBD-0101 ", 2, "marketplace", "each"),
    (527, "13:52", "CAB-0302", 15, "web", "each"),
    (528, "14:27", "HUB-0301", 2, "web", "each"),
    (529, "15:01", "KBD-0101", 5, "web", "each"),
    (530, "15:38", " MON-0201", 1, "marketplace", "each"),
    (531, "16:12", "MSE-0102", 1, "store", "pack"),
    (532, "16:50", "WEB-0401", 3, "marketplace", "each"),
    (533, "17:24", "hds-0402", 2, "marketplace", "pack"),
    (534, "18:03", "DOC-0501", 3, "web", "each"),
    (535, "18:41", "HDS-0402", 5, "marketplace", "each"),
    (536, "19:15", "MON-0201", 3, "store", "each"),
    (537, "20:02", "Kbd-0101", 4, "marketplace", "each"),
    (538, "21:30", "CAB-0302", 4, "marketplace", "each"),
]
TODAY = [
    (539, "06:10", "MSE-0102", 2, "web", "each"),
    (540, "06:48", "KBD-0101", 3, "marketplace", "each"),
    (541, "07:15", "CAB-0302", 1, "store", "pack"),
    (542, "07:40", "HDS-0402", 2, "marketplace", "each"),
    (543, "08:05", "WEB-0401", 1, "web", "each"),
    (544, "08:31", "MON-0201", 1, "marketplace", "each"),
    (545, "08:55", "HUB-0301", 2, "store", "each"),
    (546, "09:12", "KBD-0101", 1, "web", "each"),
]
# The sales system hands the last orders before a fetch over again with the
# next one. The job has a guard for that.
SENT_AGAIN = 2


def rows_of(batch, day):
    rows = []
    for number, time, sku, quantity, channel, unit in batch:
        placed_at = f"{day.isoformat()}T{time}"
        rows.append((f"SO-20{number}", placed_at, sku, quantity, channel, unit))
    return rows


def write_sales_data(target, rows):
    """What the sales system will hand over at the next fetch."""
    with open(target / "data" / "orders.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


def cron_run(target, command):
    """One run from cron: only what the job prints is kept."""
    done = subprocess.run(
        command, cwd=target, capture_output=True, text=True, check=False
    )
    stamp = datetime.now().isoformat(timespec="seconds")
    with open(target / "data" / "cron.log", "a", encoding="utf-8") as log:
        log.write(f"{stamp} order-sync exit={done.returncode} {done.stdout.strip()}\n")
    if done.returncode != 0 or done.stdout != "sync finished: OK\n":
        raise SystemExit(f"the job did not finish OK:\n{done.stdout}{done.stderr}")


def install_ormaos(target, source):
    venv = target / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    pip = [str(venv / "bin" / "python"), "-m", "pip", "install", "--quiet"]
    subprocess.run([*pip, source], check=True)


def physical_count(stock_csv, batches):
    """What is on the shelves: every order left the warehouse, once."""
    with open(stock_csv, newline="", encoding="utf-8") as handle:
        items = list(csv.DictReader(handle))
    shelf = {item["sku"]: int(item["on_hand"]) for item in items}
    pack = {item["sku"]: int(item["pack_size"]) for item in items}
    shipped = set()
    for rows in batches:
        for order_id, _, sent_sku, quantity, _, unit in sorted(rows, key=lambda r: r[1]):
            if order_id in shipped:
                continue
            shipped.add(order_id)
            sku = sent_sku.strip().upper()
            wanted = quantity * pack[sku] if unit == "pack" else quantity
            shelf[sku] -= min(wanted, shelf[sku])
    return shelf


def check_nothing_is_left(target, skipped):
    """The orders the job skipped last night must be nowhere in the folder."""
    needles = [order_id.encode() for order_id, *_ in skipped]
    needles += [sku.encode() for _, _, sku, *_ in skipped]
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
        help="install Ormaos in the folder and record last night's run",
    )
    parser.add_argument(
        "--ormaos",
        default=ORMAOS_SOURCE,
        metavar="SOURCE",
        help="what pip installs with --record (a checkout path, or the default: "
        f"{ORMAOS_SOURCE})",
    )
    parser.add_argument(
        "--from", dest="source", type=Path, default=ORDER_SYNC, help="order-sync"
    )
    args = parser.parse_args(argv)
    target = args.target.resolve()
    if target.exists():
        parser.error(f"{target} already exists")

    shutil.copytree(args.source, target, ignore=shutil.ignore_patterns(*NOT_COPIED))
    (target / "data").mkdir()
    stock_csv = args.source / "seed" / "stock.csv"
    python = sys.executable
    if args.record:
        install_ormaos(target, args.ormaos)
        python = ".venv/bin/python"
    job = [python, "job.py", "--source", "api"]
    subprocess.run(
        [python, "inventory.py", "--db", "data/inventory.db", "--create-from", stock_csv],
        cwd=target,
        check=True,
        stdout=subprocess.DEVNULL,
    )

    today = datetime.now().date()
    before = rows_of(NIGHT_BEFORE_LAST, today - timedelta(days=2))
    last_night = before[-SENT_AGAIN:] + rows_of(LAST_NIGHT, today - timedelta(days=1))
    morning = last_night[-1:] + rows_of(TODAY, today)

    write_sales_data(target, before)
    cron_run(target, job)
    write_sales_data(target, last_night)
    if args.record:
        cron_run(target, [".venv/bin/ormaos", "run", "--", *job])
    else:
        cron_run(target, job)
    write_sales_data(target, morning)

    count = physical_count(stock_csv, [before, last_night])
    with open(target / "data" / "count.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(("sku", "counted"))
        writer.writerows(sorted(count.items()))

    for cache in target.glob("__pycache__"):
        shutil.rmtree(cache)
    skipped = [row for row in last_night if row[2] != row[2].strip().upper()]
    check_nothing_is_left(target, skipped)

    conn = sqlite3.connect(target / "data" / "inventory.db")
    on_hand = dict(conn.execute("SELECT sku, on_hand FROM stock"))
    conn.close()
    wrong = sorted(sku for sku in count if on_hand[sku] != count[sku])
    print(f"morning after: {target}")
    print(f"last night: {len(last_night)} orders handed over, {len(skipped)} skipped")
    print(f"stock that differs from the count: {', '.join(wrong)}")
    print(f"recorded: {'yes, in .ormaos/' if args.record else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
