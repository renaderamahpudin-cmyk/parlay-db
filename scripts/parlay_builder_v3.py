"""Point-in-time goal model and Asian O/U settlement calculations.

This version deliberately keeps the same public API but fixes the main stability issues:
- expected-goal scaling now uses a clearer home/away baseline ratio,
- the lambda caps are controlled by a shared config,
- settlement handling keeps half-win/half-loss and pushes consistently.
"""
from collections import defaultdict, deque
import math
import re

import pandas as pd

from prediction_config import (
    H2H_WEIGHT,
    MAX_LAMBDA,
    MAX_OU_GAP,
    MAX_OU_ODDS,
    MIN_FORM_MATCHES,
    MIN_LAMBDA,
    MIN_OU_GAP,
    MIN_OU_ODDS,
    PRIOR_MATCHES,
    RECENT_MATCHES,
)


RECENT_MATCHES = RECENT_MATCHES
MIN_FORM_MATCHES = MIN_FORM_MATCHES
H2H_WEIGHT = H2H_WEIGHT
LEAGUE_BASELINE_DAYS = 730
MIN_LEAGUE_BASELINE_MATCHES = 30
PRIOR_MATCHES = PRIOR_MATCHES


TEAM_ALIASES = {
    "hjk helsinki": ["hjk", "hjk helsinki", "helsinki"],
    "vaasa vps": ["vps", "vaasa", "vaasan"],
    "kups": ["kups", "kuopio"],
    "ac oulu": ["oulu", "ac oulu"],
    "shamrock rovers": ["shamrock", "shamrock rovers"],
    "drogheda united": ["drogheda", "drogheda united"],
    "santos sp": ["santos"],
    "flamengo rj": ["flamengo"],
    "fluminense rj": ["fluminense"],
    "coritiba pr": ["coritiba"],
    "palmeiras sp": ["palmeiras"],
    "bahia ec ba": ["bahia"],
    "ceara ce": ["ceara"],
    "criciuma ec sc": ["criciuma"],
    "nautico pe": ["nautico"],
    "gremio novorizontino sp": ["novorizontino", "gremio novorizontino"],
    "atletico fc": ["atletico"],
    "real cartagena": ["cartagena"],
    "independiente valle del cauca": ["independiente"],
    "tigres fc": ["tigres"],
}


def normalize_team(name):
    return re.sub(r"\s*\[[RW]\]\s*", "", str(name or "").strip()).casefold()


def canonical_team(name):
    normalized = normalize_team(name)
    for canonical, aliases in TEAM_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            return canonical
    return normalized


def team_names_match(database_name, requested_name):
    """Match known aliases first, then conservative normalized substrings."""
    database = normalize_team(database_name)
    requested = normalize_team(requested_name)
    if not database or not requested:
        return False
    database_key = canonical_team(database)
    requested_key = canonical_team(requested)
    if database_key == requested_key:
        return True
    if len(database) >= 5 and len(requested) >= 5:
        return (
            (database in requested or requested in database)
            and abs(len(database) - len(requested)) <= max(len(database), 3)
        )
    return False


def _number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result >= 0 else None


def _record(row):
    home = str(row.get("home", row.get("HomeTeam", "")) or "").strip()
    away = str(row.get("away", row.get("AwayTeam", "")) or "").strip()
    if not home or not away:
        raise ValueError("Nama tim kandang/tandang wajib diisi.")
    return {
        "date": pd.Timestamp(row["date"]),
        "home": canonical_team(row.get("home_key", home)),
        "away": canonical_team(row.get("away_key", away)),
        "hg": int(row.get("hg", row.get("FTHG"))),
        "ag": int(row.get("ag", row.get("FTAG"))),
        "hs": _number(row.get("hs", row.get("HS"))),
        "as": _number(row.get("as", row.get("AS"))),
        "hst": _number(row.get("hst", row.get("HST"))),
        "ast": _number(row.get("ast", row.get("AST"))),
        "league": str(
            row.get("league", row.get("League", "?")) or "?"
        ).strip().casefold(),
    }


def _new_aggregate():
    return {
        "matches": 0,
        "home_goals": 0.0,
        "away_goals": 0.0,
        "home_sot": 0.0,
        "away_sot": 0.0,
        "home_sot_count": 0,
        "away_sot_count": 0,
    }


def _add_aggregate(aggregate, record):
    aggregate["matches"] += 1
    aggregate["home_goals"] += record["hg"]
    aggregate["away_goals"] += record["ag"]
    if record["hst"] is not None:
        aggregate["home_sot"] += record["hst"]
        aggregate["home_sot_count"] += 1
    if record["ast"] is not None:
        aggregate["away_sot"] += record["ast"]
        aggregate["away_sot_count"] += 1


def _safe_rate(numerator, denominator, fallback):
    return numerator / denominator if denominator > 0 else fallback


def _mean(values, weights):
    denominator = sum(weights)
    return sum(value * weight for value, weight in zip(values, weights)) / denominator


def _smoothed(observed, sample_size, prior):
    return (observed * sample_size + prior * PRIOR_MATCHES) / (sample_size + PRIOR_MATCHES)


class WalkForwardModel:
    """Online model: call predict for a date, then update after that whole date."""

    def __init__(self, recent_matches=RECENT_MATCHES, min_form_matches=MIN_FORM_MATCHES):
        if recent_matches < min_form_matches or min_form_matches < 1:
            raise ValueError("recent_matches harus >= min_form_matches >= 1.")
        self.recent_matches = recent_matches
        self.min_form_matches = min_form_matches
        self.home_form = defaultdict(lambda: deque(maxlen=recent_matches))
        self.away_form = defaultdict(lambda: deque(maxlen=recent_matches))
        self.h2h_form = defaultdict(lambda: deque(maxlen=20))
        self.league_recent = defaultdict(deque)
        self.league_all = defaultdict(_new_aggregate)
        self.global_recent = deque()
        self.global_all = _new_aggregate()
        self.last_update_date = None
        self._baseline_cache = {}

    def update(self, row):
        """Add one finished match; callers must add a date only after forecasting it."""
        record = _record(row)
        match_date = record["date"].normalize()
        if self.last_update_date is not None and match_date < self.last_update_date:
            raise ValueError("Model harus diperbarui secara kronologis.")
        record["date"] = match_date
        self.home_form[record["home"]].append(record)
        self.away_form[record["away"]].append(record)
        self.h2h_form[(record["home"], record["away"])].append(record)
        _add_aggregate(self.league_all[record["league"]], record)
        _add_aggregate(self.global_all, record)
        self.league_recent[record["league"]].append(record)
        self.global_recent.append(record)

        cutoff = match_date - pd.Timedelta(days=LEAGUE_BASELINE_DAYS)
        for queue in (self.league_recent[record["league"]], self.global_recent):
            while queue and queue[0]["date"] < cutoff:
                queue.popleft()
        self.last_update_date = match_date
        self._baseline_cache.clear()

    def _baseline(self, league, as_of):
        cache_key = (league, pd.Timestamp(as_of).normalize())
        if cache_key in self._baseline_cache:
            return self._baseline_cache[cache_key]
        league_rows = self.league_recent.get(league, ())
        league_count = len(league_rows)
        if league_count >= MIN_LEAGUE_BASELINE_MATCHES:
            aggregate = _new_aggregate()
            for row in league_rows:
                _add_aggregate(aggregate, row)
            source = "liga_2_tahun"
        else:
            aggregate = self.league_all.get(league, _new_aggregate())
            if aggregate["matches"] >= MIN_LEAGUE_BASELINE_MATCHES:
                source = "riwayat_liga"
            else:
                global_rows = [
                    row for row in self.global_recent
                    if row["date"] < as_of
                ]
                if len(global_rows) >= MIN_LEAGUE_BASELINE_MATCHES:
                    aggregate = _new_aggregate()
                    for row in global_rows:
                        _add_aggregate(aggregate, row)
                    source = "rata_global_2_tahun"
                else:
                    aggregate = self.global_all
                    source = "rata_global_arsip"

        matches = aggregate["matches"]
        home_avg = _safe_rate(aggregate["home_goals"], matches, 1.45)
        away_avg = _safe_rate(aggregate["away_goals"], matches, 1.15)
        home_conversion = _safe_rate(
            aggregate["home_goals"], aggregate["home_sot"], 0.30
        )
        away_conversion = _safe_rate(
            aggregate["away_goals"], aggregate["away_sot"], 0.27
        )
        baseline = {
            "home_goals": max(home_avg, 0.1),
            "away_goals": max(away_avg, 0.1),
            "home_sot_conversion": min(max(home_conversion, 0.08), 0.75),
            "away_sot_conversion": min(max(away_conversion, 0.08), 0.75),
            "source": source,
            "matches": matches,
        }
        self._baseline_cache[cache_key] = baseline
        return baseline

    @staticmethod
    def _form_rates(rows, side, baseline):
        if side == "home":
            goals_for_key, goals_against_key = "hg", "ag"
            shots_for_key, shots_against_key = "hst", "ast"
            conversion_for = baseline["home_sot_conversion"]
            conversion_against = baseline["away_sot_conversion"]
        else:
            goals_for_key, goals_against_key = "ag", "hg"
            shots_for_key, shots_against_key = "ast", "hst"
            conversion_for = baseline["away_sot_conversion"]
            conversion_against = baseline["home_sot_conversion"]

        weights = list(range(1, len(rows) + 1))
        goals_for = []
        goals_against = []
        for row in rows:
            scored = row[goals_for_key]
            conceded = row[goals_against_key]
            shots_for = row[shots_for_key]
            shots_against = row[shots_against_key]
            goals_for.append(
                0.75 * scored + 0.25 * shots_for * conversion_for
                if shots_for is not None else float(scored)
            )
            goals_against.append(
                0.75 * conceded + 0.25 * shots_against * conversion_against
                if shots_against is not None else float(conceded)
            )
        return (
            _mean(goals_for, weights),
            _mean(goals_against, weights),
        )

    def predict(self, home, away, as_of, league="?"):
        """Estimate independent home/away goal means using data strictly before as_of."""
        cutoff = pd.Timestamp(as_of).normalize()
        if self.last_update_date is not None and self.last_update_date >= cutoff:
            raise ValueError(
                "Kebocoran waktu: data yang dimuat mencakup tanggal pertandingan."
            )
        home_key, away_key = canonical_team(home), canonical_team(away)
        home_rows = list(self.home_form.get(home_key, ()))
        away_rows = list(self.away_form.get(away_key, ()))
        if len(home_rows) < self.min_form_matches:
            return {
                "available": False,
                "reason": "sampel_kandang_kurang",
                "home_form_count": len(home_rows),
                "away_form_count": len(away_rows),
            }
        if len(away_rows) < self.min_form_matches:
            return {
                "available": False,
                "reason": "sampel_tandang_kurang",
                "home_form_count": len(home_rows),
                "away_form_count": len(away_rows),
            }

        baseline = self._baseline(str(league or "?").strip().casefold(), cutoff)
        home_attack, home_defense = self._form_rates(home_rows, "home", baseline)
        away_attack, away_defense = self._form_rates(away_rows, "away", baseline)

        home_attack = _smoothed(home_attack, len(home_rows), baseline["home_goals"])
        home_defense = _smoothed(home_defense, len(home_rows), baseline["away_goals"])
        away_attack = _smoothed(away_attack, len(away_rows), baseline["away_goals"])
        away_defense = _smoothed(away_defense, len(away_rows), baseline["home_goals"])

        home_baseline = max(baseline["home_goals"], 0.35)
        away_baseline = max(baseline["away_goals"], 0.35)
        lambda_home = (home_attack * away_defense) / away_baseline
        lambda_away = (away_attack * home_defense) / home_baseline

        h2h_rows = [
            row for row in self.h2h_form.get((home_key, away_key), ())
            if row["date"] < cutoff
        ]
        h2h_count = len(h2h_rows)
        if h2h_count:
            h2h_home = (
                sum(row["hg"] for row in h2h_rows)
                + PRIOR_MATCHES * baseline["home_goals"]
            ) / (h2h_count + PRIOR_MATCHES)
            h2h_away = (
                sum(row["ag"] for row in h2h_rows)
                + PRIOR_MATCHES * baseline["away_goals"]
            ) / (h2h_count + PRIOR_MATCHES)
            lambda_home = (1 - H2H_WEIGHT) * lambda_home + H2H_WEIGHT * h2h_home
            lambda_away = (1 - H2H_WEIGHT) * lambda_away + H2H_WEIGHT * h2h_away

        lambda_home = min(max(lambda_home, MIN_LAMBDA), MAX_LAMBDA)
        lambda_away = min(max(lambda_away, MIN_LAMBDA), MAX_LAMBDA)
        return {
            "available": True,
            "lambda_home": lambda_home,
            "lambda_away": lambda_away,
            "expected_total": lambda_home + lambda_away,
            "home_form_count": len(home_rows),
            "away_form_count": len(away_rows),
            "h2h_before": h2h_count,
            "baseline_source": baseline["source"],
            "baseline_matches": baseline["matches"],
            "uses_shot_proxy": any(
                row["hst"] is not None for row in home_rows
            ) or any(row["ast"] is not None for row in away_rows),
        }


def total_goal_distribution(lambda_home, lambda_away, tail_tolerance=1e-12):
    """Return P(total goals=k) for the sum of independent Poisson goal counts."""
    total_rate = float(lambda_home) + float(lambda_away)
    if not math.isfinite(total_rate) or total_rate < 0:
        raise ValueError("Perkiraan gol harus berupa angka non-negatif.")
    if total_rate == 0:
        return [1.0]
    probabilities = [math.exp(-total_rate)]
    cumulative = probabilities[0]
    goals = 0
    while 1 - cumulative > tail_tolerance and goals < 200:
        goals += 1
        probabilities.append(probabilities[-1] * total_rate / goals)
        cumulative += probabilities[-1]
    mass = sum(probabilities)
    return [probability / mass for probability in probabilities]


def _settle_total(side, line, total_goals, odds):
    """Net profit per unit for an integer total on a quarter-goal line."""
    side = str(side).upper()
    line = float(line)
    if side not in {"OVER", "UNDER"} or line < 0:
        raise ValueError("Sisi atau line O/U tidak valid.")
    scaled = line * 4
    if not math.isclose(scaled, round(scaled), abs_tol=1e-8):
        raise ValueError("Line O/U harus menggunakan kelipatan 0,25.")
    if round(scaled) % 2:
        lower = math.floor(line * 2) / 2
        legs = (lower, lower + 0.5)
    else:
        legs = (line,)

    profits = []
    for leg in legs:
        if total_goals == leg:
            profits.append(0.0)
        else:
            won = total_goals > leg if side == "OVER" else total_goals < leg
            profits.append(float(odds) - 1 if won else -1.0)
    return sum(profits) / len(profits)


def settlement_distribution(lambda_home, lambda_away, side, line, odds):
    """Return full/half/push/lose settlement probabilities and expected return."""
    odds = float(odds)
    if not math.isfinite(odds) or odds <= 1:
        raise ValueError("Odds desimal harus lebih besar dari 1.")
    total_pmf = total_goal_distribution(lambda_home, lambda_away)
    category_mass = {
        "full_win": 0.0,
        "half_win": 0.0,
        "push": 0.0,
        "half_loss": 0.0,
        "full_loss": 0.0,
    }
    expected_return = 0.0
    for total_goals, probability in enumerate(total_pmf):
        profit = _settle_total(side, line, total_goals, odds)
        expected_return += probability * profit
        if profit > 0:
            key = "full_win" if math.isclose(profit, odds - 1) else "half_win"
        elif profit < 0:
            key = "full_loss" if math.isclose(profit, -1.0) else "half_loss"
        else:
            key = "push"
        category_mass[key] += probability

    win_mass = category_mass["full_win"] + 0.5 * category_mass["half_win"]
    loss_mass = category_mass["full_loss"] + 0.5 * category_mass["half_loss"]
    resolved_mass = win_mass + loss_mass + category_mass["push"]
    conditional_probability = (win_mass / resolved_mass) if resolved_mass else None
    return {
        **category_mass,
        "conditional_probability": conditional_probability,
        "expected_return": expected_return,
        "total_pmf": total_pmf,
    }


def compare_market_line(lambda_home, lambda_away, line, odds_over, odds_under):
    """Compare model settlement probabilities with a two-sided no-vig market."""
    odds_over, odds_under = float(odds_over), float(odds_under)
    if odds_over <= 1 or odds_under <= 1:
        raise ValueError("Odds O/U harus lebih besar dari 1.")
    raw_over, raw_under = 1 / odds_over, 1 / odds_under
    overround = raw_over + raw_under - 1
    market_over = raw_over / (raw_over + raw_under)
    market_under = raw_under / (raw_over + raw_under)
    results = {}
    for side, odds, market_probability in (
        ("OVER", odds_over, market_over),
        ("UNDER", odds_under, market_under),
    ):
        settlement = settlement_distribution(
            lambda_home, lambda_away, side, line, odds
        )
        model_probability = settlement["conditional_probability"]
        results[side.lower()] = {
            **settlement,
            "odds": odds,
            "market_no_vig_probability": market_probability,
            "value_gap": (
                (model_probability - market_probability) * 100
                if model_probability is not None else None
            ),
        }
    return {
        "line": float(line),
        "market_overround_pct": overround * 100,
        "market_over_no_vig_pct": market_over * 100,
        "market_under_no_vig_pct": market_under * 100,
        "over": results["over"],
        "under": results["under"],
    }


# Exported constants kept for compatibility with the rest of the project.
__all__ = [
    "WalkForwardModel",
    "compare_market_line",
    "normalize_team",
    "canonical_team",
    "team_names_match",
    "total_goal_distribution",
    "settlement_distribution",
    "MAX_OU_GAP",
    "MAX_OU_ODDS",
    "MIN_OU_GAP",
    "MIN_OU_ODDS",
    "MIN_LAMBDA",
    "MAX_LAMBDA",
]
