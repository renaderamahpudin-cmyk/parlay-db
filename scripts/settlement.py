"""Shared settlement and CSV schema for automatic and manual result tracking."""
from decimal import Decimal, InvalidOperation, ROUND_FLOOR


TRACK_COLUMNS = [
    "tanggal", "liga", "home", "away", "pick", "conf", "odds", "skor",
    "tier", "skor_home", "skor_away", "total_gol", "hasil", "profit_loss",
    "catatan", "pick_push_rate",
]


def match_key(liga, home, away):
    """Stable key shared by the draft queue and the result tracker."""
    return tuple(" ".join(str(value or "").casefold().split())
                 for value in (liga, home, away))


def _decimal(value, field):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} tidak valid: {value!r}")
    if not number.is_finite():
        raise ValueError(f"{field} tidak valid: {value!r}")
    return number


def _total_leg_profit(side, total_goals, line, odds):
    if total_goals == line:
        return Decimal("0")
    won = total_goals > line if side == "OVER" else total_goals < line
    return odds - 1 if won else Decimal("-1")


def settle_pick(pick, skor_home, skor_away, odds):
    """Return (result, net profit per unit stake), including Asian totals."""
    if isinstance(skor_home, bool) or isinstance(skor_away, bool):
        raise ValueError("Skor harus bilangan bulat non-negatif.")
    home_value = _decimal(skor_home, "Skor kandang")
    away_value = _decimal(skor_away, "Skor tandang")
    if (
        home_value < 0 or away_value < 0
        or home_value != home_value.to_integral_value()
        or away_value != away_value.to_integral_value()
    ):
        raise ValueError("Skor harus bilangan bulat non-negatif.")
    home_goals = int(home_value)
    away_goals = int(away_value)

    decimal_odds = _decimal(odds, "Odds")
    if decimal_odds <= 1:
        raise ValueError("Odds desimal harus lebih besar dari 1.")

    normalized_pick = str(pick or "").strip().upper()
    home_result = (
        "HOME" if home_goals > away_goals
        else "AWAY" if home_goals < away_goals
        else "DRAW"
    )
    if normalized_pick in {"HOME", "AWAY", "DRAW"}:
        if normalized_pick == home_result:
            return "WIN", float(decimal_odds - 1)
        return "LOSE", -1.0

    parts = normalized_pick.split(maxsplit=1)
    if len(parts) != 2 or parts[0] not in {"OVER", "UNDER"}:
        raise ValueError(f"Pick belum didukung: {pick!r}")

    side = parts[0]
    line = _decimal(parts[1], "Line")
    if line < 0:
        raise ValueError("Line tidak boleh negatif.")

    scaled_line = line * 4
    if scaled_line != scaled_line.to_integral_value():
        raise ValueError("Line O/U harus menggunakan kelipatan 0,25.")

    total_goals = Decimal(home_goals + away_goals)
    if int(scaled_line) % 2:
        lower = (line * 2).to_integral_value(rounding=ROUND_FLOOR) / 2
        legs = (lower, lower + Decimal("0.5"))
    else:
        legs = (line,)

    profit = sum(
        (_total_leg_profit(side, total_goals, leg, decimal_odds) for leg in legs),
        Decimal("0"),
    ) / len(legs)

    if profit > 0:
        result = "WIN" if profit == decimal_odds - 1 else "HALF_WIN"
    elif profit < 0:
        result = "LOSE" if profit == -1 else "HALF_LOSE"
    else:
        result = "PUSH"
    return result, float(profit)
