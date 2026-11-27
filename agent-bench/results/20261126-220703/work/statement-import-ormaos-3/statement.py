"""The bank's statement file.

One record per line, fields separated by ``|``::

    H|<account>|<date>                               the header, first line
    T|<bank id>|<date>|<amount>|<status>|<text>      a transaction
    R|<bank id>|<date>|<bank id it reverses>         a reversal

An amount is ``1250.00`` for money in and ``1250.00-`` for money out. The
status is ``B`` (booked) or ``P`` (pending). Lines that start with ``#`` are
comments. Empty lines are ignored.
"""

from dataclasses import dataclass
from datetime import date


class StatementError(ValueError):
    """The file is not a statement of this format."""


@dataclass(frozen=True)
class Record:
    kind: str
    bank_id: str
    booked_on: date
    amount_cents: int = 0
    status: str = "B"
    text: str = ""
    reverses: str = ""


def parse_amount(text):
    """``1250.00`` -> 125000, ``12.5-`` -> -1250."""
    negative = text.endswith("-")
    units, _, cents = text.rstrip("-").partition(".")
    if not units.isdigit() or not (cents + "0").isdigit() or len(cents) > 2:
        raise StatementError(f"not an amount: {text!r}")
    value = int(units) * 100 + int((cents + "00")[:2])
    return -value if negative else value


def parse_header(line):
    fields = line.strip().split("|")
    if len(fields) != 3 or fields[0] != "H":
        raise StatementError(f"not a header: {line.strip()!r}")
    return fields[1], date.fromisoformat(fields[2])


def parse_record(line):
    fields = line.split("|")
    kind = fields[0]
    if kind == "T" and len(fields) == 6:
        _, bank_id, day, amount, status, text = fields
        if status not in ("B", "P"):
            raise StatementError(f"unknown status in {line!r}")
        return Record("T", bank_id, date.fromisoformat(day), parse_amount(amount), status, text)
    if kind == "R" and len(fields) == 4:
        _, bank_id, day, reverses = fields
        return Record("R", bank_id, date.fromisoformat(day), reverses=reverses)
    raise StatementError(f"not a record: {line!r}")


def read(path):
    """The account, the date and the records of one statement file."""
    records = []
    with open(path, encoding="utf-8") as handle:
        account, day = parse_header(handle.readline())
        # Read to the end of the file: an empty line is skipped, not the end.
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            records.append(parse_record(line))
    return account, day, records
