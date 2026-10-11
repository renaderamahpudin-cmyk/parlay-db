"""Selection rules for current prediction and slip output."""
import math
import os
import re
import sys

# Add scripts directory to path so we can import prediction_config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prediction_config import MAX_OU_GAP, MAX_OU_ODDS, MIN_OU_GAP, MIN_OU_ODDS


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
        confidence = float(pick.get("pick_conf"))
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(gap)
        and math.isfinite(odds)
        and math.isfinite(confidence)
        and MIN_OU_GAP <= gap <= MAX_OU_GAP
        and MIN_OU_ODDS <= odds <= MAX_OU_ODDS
    )
