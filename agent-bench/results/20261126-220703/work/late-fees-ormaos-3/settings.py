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
    # LATE_FEES_PAUSE in the environment wins over the file. It is parsed as a
    # boolean (1/0, yes/no, true/false, on/off): any non-empty string used to
    # count as "pause", so LATE_FEES_PAUSE=0 silently paused the job.
    env_pause = os.environ.get("LATE_FEES_PAUSE", "").strip()
    if env_pause:
        value = env_pause.lower()
        if value not in parser.BOOLEAN_STATES:
            raise ValueError(f"LATE_FEES_PAUSE={env_pause!r} is not a boolean")
        pause = parser.BOOLEAN_STATES[value]
    else:
        pause = job.getboolean("pause", fallback=False)
    return Settings(
        pause=pause,
        daily_basis_points=fees.getint("daily_basis_points"),
        minimum_cents=fees.getint("minimum_cents"),
        cap_percent=fees.getint("cap_percent"),
        grace_days={plan: int(days) for plan, days in parser["grace_days"].items()},
    )
