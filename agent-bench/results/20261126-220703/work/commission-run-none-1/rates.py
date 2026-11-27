"""The commission rates.

The table ``rate_table`` has a rate, in basis points, for a rep and a
product line. The rep ``*`` is the rate of a product line for every rep who
has no rate of their own for it.
"""

BIG_DEAL_CENTS = 1_000_000
BIG_DEAL_EXTRA_BP = 50

# The quarter-end run has tens of thousands of deals: a rate is read once a run.
# Keyed by (rep, product line): a rep can have different rates per line.
_looked_up = {}


def rate_bp(conn, rep_id, product_line):
    """The rate of a rep for a product line, in basis points."""
    key = (rep_id, product_line)
    if key not in _looked_up:
        row = conn.execute(
            "SELECT rate_bp FROM rate_table WHERE rep_id = ? AND product_line = ?",
            (rep_id, product_line),
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT rate_bp FROM rate_table WHERE rep_id = '*' AND product_line = ?",
                (product_line,),
            ).fetchone()
        if row is None:
            raise KeyError(f"no rate for product line {product_line!r}")
        _looked_up[key] = row[0]
    return _looked_up[key]


def commission_cents(conn, deal, rep_id):
    """The commission of one rep on one deal, rounded down to a cent."""
    rate = rate_bp(conn, rep_id, deal.product_line)
    if deal.amount_cents > BIG_DEAL_CENTS:
        rate += BIG_DEAL_EXTRA_BP
    return deal.share_cents * rate // 10000
