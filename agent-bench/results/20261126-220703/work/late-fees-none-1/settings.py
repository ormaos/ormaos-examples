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
    """The pause switch: LATE_FEES_PAUSE if set, else ``pause`` in settings.ini.

    The variable is parsed like the file (1/yes/true/on, 0/no/false/off), so
    LATE_FEES_PAUSE=0 means "not paused". Any other value is an error rather
    than a silent guess, since a wrong guess either skips a night of fees or
    charges during maintenance.
    """
    value = os.environ.get("LATE_FEES_PAUSE")
    if value is None or value.strip() == "":
        return job.getboolean("pause", fallback=False)
    key = value.strip().lower()
    if key not in configparser.ConfigParser.BOOLEAN_STATES:
        raise ValueError(f"LATE_FEES_PAUSE={value!r} is not a yes/no value")
    return configparser.ConfigParser.BOOLEAN_STATES[key]


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
