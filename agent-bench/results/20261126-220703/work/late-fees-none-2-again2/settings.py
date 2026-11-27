"""The settings of the job: settings.ini, and the pause switch."""

import configparser
import os
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "settings.ini"


@dataclass(frozen=True)
class Settings:
    pause: bool
    daily_basis_points: int
    minimum_cents: int
    cap_percent: int
    grace_days: dict


def _pause(job):
    """LATE_FEES_PAUSE in the environment, if set, else `pause` in the file.

    Both are read as booleans (1/yes/true/on, 0/no/false/off): the variable
    is a string, so "0" or "no" must not count as a pause just for being set.
    """
    value = os.environ.get("LATE_FEES_PAUSE", "").strip()
    if not value:
        return job.getboolean("pause", fallback=False)
    try:
        return configparser.ConfigParser.BOOLEAN_STATES[value.lower()]
    except KeyError:
        raise ValueError(f"LATE_FEES_PAUSE={value!r} is not a yes/no value") from None


def load(path=DEFAULT_FILE):
    parser = configparser.ConfigParser()
    with open(path, encoding="utf-8") as handle:
        parser.read_file(handle)
    job, fees = parser["job"], parser["fees"]
    return Settings(
        # LATE_FEES_PAUSE in the environment wins over the file.
        pause=_pause(job),
        daily_basis_points=fees.getint("daily_basis_points"),
        minimum_cents=fees.getint("minimum_cents"),
        cap_percent=fees.getint("cap_percent"),
        grace_days={plan: int(days) for plan, days in parser["grace_days"].items()},
    )
