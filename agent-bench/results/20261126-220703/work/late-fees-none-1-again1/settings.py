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


def _pause_from_env(default):
    """LATE_FEES_PAUSE as a boolean; unset or empty means: use the file.

    Any non-empty string is truthy in Python, so "0" or "no" used to pause
    the job. Parse it like the .ini file does, and refuse anything else.
    """
    raw = os.environ.get("LATE_FEES_PAUSE", "").strip().lower()
    if not raw:
        return default
    if raw in configparser.ConfigParser.BOOLEAN_STATES:
        return configparser.ConfigParser.BOOLEAN_STATES[raw]
    raise ValueError(f"LATE_FEES_PAUSE={raw!r} is not a yes/no value")


def load(path=DEFAULT_FILE):
    parser = configparser.ConfigParser()
    with open(path, encoding="utf-8") as handle:
        parser.read_file(handle)
    job, fees = parser["job"], parser["fees"]
    return Settings(
        # LATE_FEES_PAUSE in the environment wins over the file.
        pause=_pause_from_env(job.getboolean("pause", fallback=False)),
        daily_basis_points=fees.getint("daily_basis_points"),
        minimum_cents=fees.getint("minimum_cents"),
        cap_percent=fees.getint("cap_percent"),
        grace_days={plan: int(days) for plan, days in parser["grace_days"].items()},
    )
