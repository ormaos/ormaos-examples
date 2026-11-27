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


def load(path=DEFAULT_FILE):
    parser = configparser.ConfigParser()
    with open(path, encoding="utf-8") as handle:
        parser.read_file(handle)
    job, fees = parser["job"], parser["fees"]
    return Settings(
        pause=_pause(job),
        daily_basis_points=fees.getint("daily_basis_points"),
        minimum_cents=fees.getint("minimum_cents"),
        cap_percent=fees.getint("cap_percent"),
        grace_days={plan: int(days) for plan, days in parser["grace_days"].items()},
    )


def _pause(job):
    """LATE_FEES_PAUSE in the environment wins over the file, when it is set.

    Both are read as booleans (yes/no, 1/0, true/false, on/off): a non-empty
    string such as "0" or "no" must not count as a pause. An unrecognised
    value is an error (ValueError, so the job fails), never a silent pause.
    """
    raw = os.environ.get("LATE_FEES_PAUSE", "").strip()
    if raw:
        value = configparser.ConfigParser.BOOLEAN_STATES.get(raw.lower())
        if value is None:
            raise ValueError(f"LATE_FEES_PAUSE={raw!r} is not a boolean")
        return value
    return job.getboolean("pause", fallback=False)
