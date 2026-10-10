"""Selection rules for current prediction and slip output."""
import math
import re


MIN_OU_GAP = 5.0
MIN_OU_ODDS = 1.2
MAX_OU_ODDS = 4.0
MAX_OU_GAP = 40.0


_OU_PICK_RE = re.compile(r"^(OVER|UNDER)\s+\d+(?:\.\d+)?$")


def is_over_under_pick(pick):
    """Recognize O/U records, including legacy draft rows without pick_jenis."""
    if not isinstance(pick, dict):
        return False
    return bool(_OU_PICK_RE.fullmatch(str(pick.get("pick", "")).strip().upper()))


def is_eligible_ou_pick(pick):
    """Only admit quoted O/U picks with a finite, plausible positive value gap."""
    if not isinstance(pick, dict):
        return False
    if str(pick.get("pick_jenis", "")).strip().upper() != "OU":
        return False
    if not is_over_under_pick(pick):
        return False

    try:
        gap = float(pick.get("value_gap"))
        odds = float(pick.get("pick_odds"))
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(gap)
        and math.isfinite(odds)
        and MIN_OU_GAP <= gap <= MAX_OU_GAP
        and MIN_OU_ODDS <= odds <= MAX_OU_ODDS
    )
