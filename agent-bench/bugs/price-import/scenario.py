"""The morning after the supplier's list had a price that is not a number.

Last night the supplier's list had ``on request`` as the price of one
article. The converter stopped at that row; the job loaded the rows before
it and printed "price import finished: OK". This morning the supplier put a
price there, and its sync replaced the list: last night's list is gone, and
most prices in the catalog are not the list's.
"""

import sqlite3

NAME = "price-import"
SAYS = "price import finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's price import said OK, but this morning many prices in the "
    "catalog are not the prices of the supplier's list (data/supplier/pricelist.csv)."
)
HEADER = "article;description;price;currency;pack"
NOT_A_NUMBER = "ART-2109"
NO_LONGER_SOLD = "ART-2115"
NEW_ARTICLE = "ART-2125"

# (sku, name, cents of one pack three days ago, pieces in a pack)
PRODUCTS = [
    ("ART-2101", "Hex bolt M8x40", 1890, 100),
    ("ART-2102", "Hex nut M8", 940, 100),
    ("ART-2103", "Washer M8", 420, 100),
    ("ART-2104", "Wood screw 4x40", 1250, 200),
    ("ART-2105", "Wall plug 8 mm", 780, 100),
    ("ART-2106", "Cable tie 200 mm", 560, 100),
    ("ART-2107", "Drill bit 6 mm HSS", 345, 1),
    ("ART-2108", "Drill bit 8 mm HSS", 495, 1),
    ("ART-2109", "Angle bracket 60 mm", 2360, 20),
    ("ART-2110", "Hinge 80 mm steel", 1980, 10),
    ("ART-2111", "Door handle set", 2450, 1),
    ("ART-2112", "Padlock 40 mm", 1190, 1),
    ("ART-2113", "Sandpaper P120 sheet", 2250, 50),
    ("ART-2114", "Masking tape 30 mm", 3480, 12),
    ("ART-2115", "Wood glue 250 ml", 465, 1),
    ("ART-2116", "Silicone clear 300 ml", 689, 1),
    ("ART-2117", "Paint brush 50 mm", 529, 1),
    ("ART-2118", "Roller sleeve 25 cm", 2390, 5),
    ("ART-2119", "Spirit level 60 cm", 1795, 1),
    ("ART-2120", "Tape measure 5 m", 899, 1),
    ("ART-2121", "Work gloves pair", 11880, 12),
    ("ART-2122", "Safety glasses", 649, 1),
    ("ART-2123", "Extension lead 5 m", 1299, 1),
    ("ART-2124", "LED bulb E27 9 W", 1990, 10),
]


def continental(cents):
    """123450 -> ``1.234,50``."""
    units, rest = divmod(cents, 100)
    return f"{units:,}".replace(",", ".") + f",{rest:02d}"


def pack_cents(night):
    """sku -> cents of one pack, on the list of a night (1, 2 or 3)."""
    prices = {}
    for index, (sku, _, cents, _) in enumerate(PRODUCTS):
        for step in range(1, night + 1):
            cents += ((index * 7 + step * 5) % 9 - 3) * 10 * (1 if (index + step) % 4 else 0)
        prices[sku] = cents
    return prices


def list_text(night, not_a_number=False, header=HEADER):
    """The supplier's list of a night. Night 2 is last night's."""
    prices = pack_cents(night)
    lines = [header]
    for sku, name, _, pack in PRODUCTS:
        price = continental(prices[sku])
        if night >= 2 and sku == NO_LONGER_SOLD:
            price = "0,00"
        if not_a_number and sku == NOT_A_NUMBER:
            price = "on request"
        lines.append(f"{sku};{name};{price};EUR;{pack}")
    if night >= 2:
        lines.append(f"{NEW_ARTICLE};Head torch;1.049,00;EUR;100")
    lines.append("ART-9001;Import duty sample;12,00;USD;1")
    return "\n".join(lines) + "\n"


def piece(cents, pack):
    return (cents * 2 + pack) // (2 * pack)  # half up


def expected(night, without=()):
    """The catalog after the list of a night was taken over: sku -> (cents, active)."""
    prices = pack_cents(night)
    before = pack_cents(night - 1)
    rows = {}
    for sku, _, _, pack in PRODUCTS:
        rows[sku] = (piece(prices[sku], pack), 1)
        if sku in without or (night >= 2 and sku == NO_LONGER_SOLD):
            rows[sku] = (piece(before[sku], pack), 0 if sku == NO_LONGER_SOLD else 1)
    if night >= 2 and NEW_ARTICLE not in without:
        rows[NEW_ARTICLE] = (piece(104900, 100), 0)
    return rows


def sync(world, text):
    """The supplier's sync: it replaces the list."""
    folder = world.data / "supplier"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pricelist.csv").write_text(text, encoding="utf-8")


def play(world, last_night=None, corrected=True):
    world.data.mkdir(exist_ok=True)
    world.run(["catalog.py", "--create"])
    conn = sqlite3.connect(world.data / "catalog.db")
    with conn:
        conn.executemany(
            "INSERT INTO products VALUES (?, ?, ?, 1)",
            [(sku, name, piece(cents, pack), ) for sku, name, cents, pack in PRODUCTS],
        )
    conn.close()
    sync(world, list_text(1))
    world.cron(["job.py"], says=SAYS)
    sync(world, list_text(2, not_a_number=True) if last_night is None else last_night)
    done = world.cron(["job.py"], bad=True, says=SAYS if last_night is None else None)
    if corrected:
        sync(world, list_text(2))
    world.clean()
    return done


def catalog(folder):
    conn = sqlite3.connect(folder / "data" / "catalog.db")
    rows = {sku: (cents, active) for sku, _, cents, active in conn.execute("SELECT * FROM products")}
    conn.close()
    return rows


def data_left(folder):
    staging = (folder / "data" / "staging.csv").read_text(encoding="utf-8")
    return [sorted(catalog(folder).items()), staging]


def wrong(folder):
    got, want = catalog(folder), expected(2)
    return sorted(sku for sku in want if got.get(sku) != want[sku])


def gone(world):
    return ["on request"]
