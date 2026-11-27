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
    """LATE_FEES_PAUSE wins over the file, read as a boolean ("0"/"no" mean not paused)."""
    raw = os.environ.get("LATE_FEES_PAUSE")
    if raw is None or raw.strip() == "":
        return job.getboolean("pause", fallback=False)
    value = raw.strip().lower()
    if value not in configparser.ConfigParser.BOOLEAN_STATES:
        raise ValueError(f"LATE_FEES_PAUSE={raw!r} is not a yes/no value")
    return configparser.ConfigParser.BOOLEAN_STATES[value]


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
