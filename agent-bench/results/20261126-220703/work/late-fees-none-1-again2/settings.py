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


_BOOLEANS = configparser.ConfigParser.BOOLEAN_STATES  # 1/yes/true/on, 0/no/false/off


def _env_pause():
    """LATE_FEES_PAUSE as a boolean, or None when it is unset or empty.

    Any non-empty string used to count as "pause", so LATE_FEES_PAUSE=0 or
    =no paused the job. An unrecognised value is an error, not a guess.
    """
    raw = os.environ.get("LATE_FEES_PAUSE", "").strip()
    if not raw:
        return None
    try:
        return _BOOLEANS[raw.lower()]
    except KeyError:
        raise ValueError(f"LATE_FEES_PAUSE={raw!r} is not a boolean (use 1/0, yes/no)") from None


def load(path=DEFAULT_FILE):
    parser = configparser.ConfigParser()
    with open(path, encoding="utf-8") as handle:
        parser.read_file(handle)
    job, fees = parser["job"], parser["fees"]
    # LATE_FEES_PAUSE in the environment wins over the file.
    pause = _env_pause()
    if pause is None:
        pause = job.getboolean("pause", fallback=False)
    return Settings(
        pause=pause,
        daily_basis_points=fees.getint("daily_basis_points"),
        minimum_cents=fees.getint("minimum_cents"),
        cap_percent=fees.getint("cap_percent"),
        grace_days={plan: int(days) for plan, days in parser["grace_days"].items()},
    )
