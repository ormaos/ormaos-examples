"""The morning after members of one household bought on the same day.

Members of a household may share an e-mail address. Last night's purchases
file had purchases, with their member numbers, of members who share their
address with someone else. The job printed "points finished: OK" and
deleted the file. This morning the inbox is empty (the next file comes
tonight), and some members' points are not the sum of their grants.
"""

import sqlite3
from datetime import date, timedelta

NAME = "points-grant"
SAYS = "points finished: OK"
RUNS_WITH = "python3 job.py"
SYMPTOM = (
    "Last night's points run said OK, but this morning the points of some members "
    "are not the sum of their grants (python3 members.py --check)."
)
MULTIPLIER_PERCENT = {"silver": 100, "gold": 150, "platinum": 200}

# (member, name, e-mail address, tier, points before)
MEMBERS = [
    ("M-1040", "Ana Reis", "ana.reis@example.org", "gold", 310),
    ("M-1041", "Bruno Lage", "bruno@lage.example", "silver", 45),
    ("M-1042", "Carla Mota", "casa.mota@example.org", "platinum", 1280),
    ("M-1043", "Diogo Mota", "casa.mota@example.org", "silver", 60),
    ("M-1044", "Eva Pinto", "eva.pinto@example.org", "silver", 0),
    ("M-1045", "Filipe Sá", "filipe.sa@example.org", "gold", 512),
    ("M-1046", "Guida Luz", "guida@luz.example", "silver", 18),
    ("M-1047", "Hugo Neves", "hugo.neves@example.org", "platinum", 2040),
    ("M-1048", "Inês Faro", "ines.faro@example.org", "gold", 77),
    ("M-1049", "João Vale", "joao.vale@example.org", "silver", 230),
    ("M-1050", "Lara Brito", "familia.brito@example.org", "gold", 640),
    ("M-1051", "Marco Brito", "familia.brito@example.org", "silver", 95),
    ("M-1052", "Nuno Brito", "familia.brito@example.org", "silver", 12),
    ("M-1053", "Olga Paz", "olga.paz@example.org", "silver", 5),
]
# (purchase, member or "" from an old till, e-mail address, cents, store)
NIGHT_BEFORE_LAST = [
    ("P-70101", "M-1040", "ana.reis@example.org", 4590, "centre"),
    ("P-70102", "", "bruno@lage.example", 1220, "harbour"),
    ("P-70103", "M-1045", "filipe.sa@example.org", 8999, "centre"),
    ("P-70104", "M-1047", "hugo.neves@example.org", 15000, "north"),
    ("P-70105", "", "guida@luz.example", 450, "harbour"),
    ("P-70106", "M-1049", "joao.vale@example.org", 2675, "north"),
    ("P-70107", "M-1053", "olga.paz@example.org", -1500, "centre"),
    ("P-70108", "", "nobody@example.org", 3000, "harbour"),
    ("P-70109", "M-1048", "ines.faro@example.org", 6240, "centre"),
    ("P-70110", "M-1044", "eva.pinto@example.org", 1999, "north"),
]
LAST_NIGHT = [
    ("P-70110", "M-1044", "eva.pinto@example.org", 1999, "north"),
    ("P-70111", "M-1041", "bruno@lage.example", 3350, "centre"),
    ("P-70112", "M-1042", "casa.mota@example.org", 12480, "centre"),
    ("P-70113", "", "guida@luz.example", 2100, "harbour"),
    ("P-70114", "M-1051", "familia.brito@example.org", 5600, "north"),
    ("P-70115", "M-1040", "ana.reis@example.org", -2000, "centre"),
    ("P-70116", "M-1047", "hugo.neves@example.org", 760, "north"),
    ("P-70117", "M-1043", "casa.mota@example.org", 1840, "centre"),
    ("P-70118", "M-1049", "joao.vale@example.org", 499, "north"),
    ("P-70119", "", "olga.paz@example.org", 3120, "harbour"),
    ("P-70120", "M-1050", "familia.brito@example.org", -9000, "north"),
    ("P-70121", "M-1045", "filipe.sa@example.org", 2250, "centre"),
    ("P-70122", "M-1048", "ines.faro@example.org", 1675, "centre"),
]
# The same night without the households that share an address.
QUIET_NIGHT = [row for row in LAST_NIGHT if row[1] not in ("M-1042", "M-1043", "M-1050", "M-1051")]


def drop(world, day, rows):
    """The tills' export: one file in the inbox."""
    inbox = world.folder / "inbox"
    inbox.mkdir(exist_ok=True)
    lines = ["purchase_id,member_id,email,amount_cents,store"]
    lines += [",".join(map(str, row)) for row in rows]
    name = f"purchases-{day.strftime('%Y%m%d')}.csv"
    (inbox / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def play(world, last_night=LAST_NIGHT):
    today = date.today()
    start, before, yesterday = (today - timedelta(days=ago) for ago in (30, 2, 1))
    world.data.mkdir(exist_ok=True)
    world.run(["members.py", "--create"])
    conn = sqlite3.connect(world.data / "members.db")
    with conn:
        conn.executemany("INSERT INTO members VALUES (?, ?, ?, ?, ?)", MEMBERS)
        conn.executemany(
            "INSERT INTO grants VALUES (?, ?, ?, ?)",
            [(f"OPENING-{m[0]}", m[0], m[4], start.isoformat()) for m in MEMBERS if m[4]],
        )
    conn.close()
    drop(world, before, NIGHT_BEFORE_LAST)
    world.cron(["job.py", "--date", before.isoformat()], says=SAYS)
    drop(world, yesterday, last_night)
    done = world.cron(["job.py", "--date", yesterday.isoformat()], bad=True, says=SAYS)
    world.clean()
    return done


def expected(batches):
    """By the rules of the README: (member -> points, purchase -> (member, points))."""
    points = {m[0]: m[4] for m in MEMBERS}
    tier = {m[0]: m[3] for m in MEMBERS}
    by_email = {}
    for member in MEMBERS:
        by_email.setdefault(member[2], member[0])
    grants = {}
    for batch in batches:
        for purchase, member, email, cents, _ in batch:
            member = member or by_email.get(email)
            if purchase in grants or member not in points or abs(cents) < 500:
                continue
            earned = abs(cents) // 100 * MULTIPLIER_PERCENT[tier[member]] // 100
            earned = earned if cents > 0 else max(-earned, -points[member])
            if earned:
                grants[purchase] = (member, earned)
                points[member] += earned
    return points, grants


def state(folder):
    conn = sqlite3.connect(folder / "data" / "members.db")
    points = dict(conn.execute("SELECT member_id, points FROM members"))
    grants = {
        p: (m, n) for p, m, n in conn.execute("SELECT purchase_id, member_id, points FROM grants")
        if not p.startswith("OPENING-")
    }
    conn.close()
    return points, grants


def data_left(folder):
    points, grants = state(folder)
    return [sorted(points.items()), sorted(grants.items())]


def wrong(folder):
    if list((folder / "inbox").glob("*")):
        raise SystemExit("the inbox is not empty")
    points, _ = state(folder)
    want, _ = expected([NIGHT_BEFORE_LAST, LAST_NIGHT])
    return sorted(m for m in want if points[m] != want[m])


def gone(world):
    """The amounts of last night's purchases by members who share an address."""
    return [f",{row[3]}," for row in LAST_NIGHT if row not in QUIET_NIGHT]
