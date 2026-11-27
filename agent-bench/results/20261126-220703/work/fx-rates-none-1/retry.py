"""Ask the feed again when it is busy for a moment."""

import logging
import os
import time

import feed

ATTEMPTS = int(os.environ.get("FX_RATES_ATTEMPTS", "3"))
WAIT_SECONDS = float(os.environ.get("FX_RATES_WAIT_SECONDS", "0.2"))
# The answers that mean "busy, ask again": bad gateway, unavailable, timeout.
# Parsed to ints: FeedError.status is the HTTP code as an int.
RETRY_STATUSES = frozenset(
    int(status)
    for status in os.environ.get("FX_RATES_RETRY_STATUSES", "502,503,504").split(",")
    if status.strip()
)

log = logging.getLogger("fx_rates.retry")


def worth_retrying(error):
    return error.status in RETRY_STATUSES


def call(function, *args):
    """Call ``function``; on a busy feed wait and call again, a few times."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return function(*args)
        except feed.FeedError as error:
            if attempt == ATTEMPTS or not worth_retrying(error):
                raise
            log.info("attempt %d: %s, asking again", attempt, error)
            time.sleep(WAIT_SECONDS * attempt)
