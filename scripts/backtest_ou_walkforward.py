"""Chronological, point-in-time walk-forward backtest for O/U forecasts."""
import argparse
from bisect import bisect_left
from collections import Counter, defaultdict
import math
import os
import sys
import warnings

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pick_policy import MAX_OU_GAP, MAX_OU_ODDS, MIN_OU_GAP, MIN_OU_ODDS
from ou_model import (
    WalkForwardModel,
    compare_market_line,
    total_goal_distribution,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

DATA_FILE = "data/football_data/all_football_data.csv"
DEFAULT_OUTPUT = "generated-artifacts/backtest_ou_poisson_walkforward.csv"
MIN_H2H = 5
DEFAULT_TEST_FRACTION = 0.20
DEFAULT_SUMMARY_OUTPUT = "generated-artifacts/backtest_ou_poisson_summary.csv"
ODDS_BANDS = ((1.2, 1.5), (1.5, 1.8), (1.8, 2.1), (2.1, 2.5), (2.5, 4.0))
GAP_THRESHOLDS = (0, 2.5, 5, 7.5, 10, 15)
ODDS_COLUMNS = (
    ("Avg", "avg_over_odds", "avg_under_odds"),
    ("B365", "b365_over_odds", "b365_under_odds"),
)


def prepare_matches(raw):
    """Normalize the football-data archive while preserving its real O/U odds."""
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {', '.join(sorted(missing))}")

    source = raw.copy()
    date_values = source["Date"].astype("string").str.strip()
    iso_date_mask = date_values.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}")
    parsed_dates = pd.Series(pd.NaT, index=source.index, dtype="datetime64[ns]")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Could not infer format")
        parsed_dates.loc[iso_date_mask] = pd.to_datetime(
            date_values.loc[iso_date_mask],
            errors="coerce",
            yearfirst=True,
            dayfirst=False,
        )
        parsed_dates.loc[~iso_date_mask] = pd.to_datetime(
            date_values.loc[~iso_date_mask],
            errors="coerce",
            dayfirst=True,
        )
    source["date"] = parsed_dates
    source["hg"] = pd.to_numeric(source["FTHG"], errors="coerce")
    source["ag"] = pd.to_numeric(source["FTAG"], errors="coerce")
    source["home"] = source["HomeTeam"].astype("string").str.strip()
    source["away"] = source["AwayTeam"].astype("string").str.strip()
    source["league"] = (
        source["League"].astype("string").str.strip()
        if "League" in source else "?"
    )

    for output_column, input_column in (
        ("avg_over_odds", "Avg>2.5"),
        ("avg_under_odds", "Avg<2.5"),
        ("b365_over_odds", "B365>2.5"),
        ("b365_under_odds", "B365<2.5"),
    ):
        source[output_column] = pd.to_numeric(
            source[input_column], errors="coerce"
        ) if input_column in source else float("nan")

    for output_column, input_column in (
        ("hs", "HS"), ("as", "AS"), ("hst", "HST"), ("ast", "AST"),
    ):
        source[output_column] = pd.to_numeric(
            source[input_column], errors="coerce"
        ) if input_column in source else float("nan")

    valid_scores = (
        source["hg"].notna()
        & source["ag"].notna()
        & (source["hg"] >= 0)
        & (source["ag"] >= 0)
        & (source["hg"] % 1 == 0)
        & (source["ag"] % 1 == 0)
    )
    valid = (
        source["date"].notna()
        & source["home"].notna()
        & source["away"].notna()
        & source["home"].ne("")
        & source["away"].ne("")
        & valid_scores
    )
    result = source.loc[valid, [
        "date", "home", "away", "hg", "ag", "league",
        "hs", "as", "hst", "ast",
        "avg_over_odds", "avg_under_odds", "b365_over_odds", "b365_under_odds",
    ]].copy()
    result["hg"] = result["hg"].astype(int)
    result["ag"] = result["ag"].astype(int)
    result["league"] = result["league"].fillna("?").astype(str)
    result["home_key"] = result["home"].str.casefold()
    result["away_key"] = result["away"].str.casefold()

    # If a source contains a duplicate fixture, retain one historical outcome.
    result = result.drop_duplicates(
        subset=["date", "home_key", "away_key"], keep="first"
    )
    return result.sort_values(
        ["date", "home_key", "away_key"]
    ).reset_index(drop=True)


def load_matches(path=DATA_FILE):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data historis tidak ditemukan: {path}")
    wanted_columns = {
        "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "League",
        "HS", "AS", "HST", "AST",
        "Avg>2.5", "Avg<2.5", "B365>2.5", "B365<2.5",
    }
    raw = pd.read_csv(
        path,
        low_memory=False,
        usecols=lambda column: column in wanted_columns,
    )
    return prepare_matches(raw)


def _pair_key(home, away):
    return tuple(sorted((str(home).casefold().strip(), str(away).casefold().strip())))


def build_h2h_index(matches):
    """Index pair outcomes by date with prefix sums for fast point-in-time reads."""
    grouped = defaultdict(list)
    for row in matches.itertuples(index=False):
        pair = _pair_key(row.home_key, row.away_key)
        grouped[pair].append((row.date, int(row.hg + row.ag > 2.5)))

    index = {}
    for pair, entries in grouped.items():
        entries.sort(key=lambda item: item[0])
        dates = []
        over_prefix = [0]
        for date, over_result in entries:
            dates.append(date)
            over_prefix.append(over_prefix[-1] + over_result)
        index[pair] = (dates, over_prefix)
    return index


def history_summary_before(index, home, away, as_of):
    """Return H2H count and O2.5 count strictly before the target's date."""
    pair = _pair_key(home, away)
    if pair not in index:
        return 0, 0
    dates, over_prefix = index[pair]
    end = bisect_left(dates, pd.Timestamp(as_of))
    return end, over_prefix[end]


def _valid_odds(value):
    try:
        odds = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(odds) or odds <= 1:
        return None
    return odds


def market_odds(row):
    """Prefer the archive's average prices; use B365 only as a complete pair."""
    for source, over_column, under_column in ODDS_COLUMNS:
        over_odds = _valid_odds(row.get(over_column))
        under_odds = _valid_odds(row.get(under_column))
        if over_odds is not None and under_odds is not None:
            return source, over_odds, under_odds
    return None


def _score_forecast(row, model):
    """Forecast one fixture from the model state available before its date."""
    prediction = model.predict(
        row["home"], row["away"], row["date"], league=row["league"]
    )
    actual_over = int(row["hg"] + row["ag"] > 2.5)
    detail = {
        "date": pd.Timestamp(row["date"]).date().isoformat(),
        "league": row["league"],
        "home": row["home"],
        "away": row["away"],
        "home_form_n": prediction.get("home_form_count", 0),
        "away_form_n": prediction.get("away_form_count", 0),
        "h2h_before": prediction.get("h2h_before", 0),
        "baseline_source": prediction.get("baseline_source", ""),
        "lambda_home": None,
        "lambda_away": None,
        "expected_total_goals": None,
        "model_over25_pct": None,
        "brier_over25": None,
        "actual_total": int(row["hg"] + row["ag"]),
        "actual_ou25": "OVER" if actual_over else "UNDER",
        "pick": "",
        "pick_conf": None,
        "market_odds": None,
        "market_source": "",
        "market_implied_raw": None,
        "market_implied_no_vig": None,
        "market_overround_pct": None,
        "value_gap": None,
        "candidate_pick": "",
        "candidate_odds": None,
        "candidate_expected_return": None,
        "expected_profit_unit": None,
        "won": None,
        "settlement": "",
        "profit_unit": None,
        "skip_reason": "",
    }
    if not prediction["available"]:
        detail["skip_reason"] = prediction["reason"]
        return detail

    lambda_home = prediction["lambda_home"]
    lambda_away = prediction["lambda_away"]
    detail.update({
        "lambda_home": round(lambda_home, 4),
        "lambda_away": round(lambda_away, 4),
        "expected_total_goals": round(lambda_home + lambda_away, 4),
        "home_form_n": prediction["home_form_count"],
        "away_form_n": prediction["away_form_count"],
        "h2h_before": prediction["h2h_before"],
        "baseline_source": prediction["baseline_source"],
    })

    prices = market_odds(row)
    if prices is not None:
        market_source, odds_over, odds_under = prices
        comparison = compare_market_line(
            lambda_home, lambda_away, 2.5, odds_over, odds_under
        )
        model_over_probability = sum(
            comparison["over"]["total_pmf"][3:]
        )
    else:
        # Calibration is still measured for every eligible forecast even if
        # the historical archive did not record O/U prices for that match.
        model_over_probability = sum(
            total_goal_distribution(lambda_home, lambda_away)[3:]
        )

    detail["model_over25_pct"] = round(model_over_probability * 100, 2)
    detail["brier_over25"] = (model_over_probability - actual_over) ** 2

    if prices is None:
        detail["skip_reason"] = "odds_ou_tidak_tersedia"
        return detail

    market_source, odds_over, odds_under = prices
    comparison = compare_market_line(
        lambda_home, lambda_away, 2.5, odds_over, odds_under
    )
    detail["market_source"] = market_source
    options = [
        ("OVER", odds_over, comparison["over"]),
        ("UNDER", odds_under, comparison["under"]),
    ]
    best = max(options, key=lambda item: (
        item[2]["expected_return"], item[2]["value_gap"]
    ))
    side, odds, metrics = best
    detail["market_overround_pct"] = round(
        comparison["market_overround_pct"], 2
    )
    detail["market_implied_raw"] = round(100 / odds, 2)
    detail["market_implied_no_vig"] = round(
        metrics["market_no_vig_probability"] * 100, 2
    )
    detail["value_gap"] = metrics["value_gap"]
    detail["candidate_pick"] = f"{side} 2.5"
    detail["candidate_odds"] = round(odds, 2)
    detail["candidate_expected_return"] = round(
        metrics["expected_return"], 5
    )
    if metrics["value_gap"] < MIN_OU_GAP:
        detail["skip_reason"] = "gap_di_bawah_minimum"
        return detail
    if metrics["value_gap"] > MAX_OU_GAP:
        detail["skip_reason"] = "gap_di_atas_batas_wajar"
        return detail
    if not MIN_OU_ODDS <= odds <= MAX_OU_ODDS:
        detail["skip_reason"] = "odds_di_luar_batas"
        return detail
    if metrics["expected_return"] <= 0:
        detail["skip_reason"] = "expected_return_tidak_positif"
        return detail

    side_result = (
        "OVER 2.5" if actual_over else "UNDER 2.5"
    )
    settlement = "WIN" if side_result == f"{side} 2.5" else "LOSE"
    won = settlement == "WIN"
    detail.update({
        "pick": f"{side} 2.5",
        "pick_conf": round(
            metrics["conditional_probability"] * 100, 2
        ),
        "market_odds": round(odds, 2),
        "expected_profit_unit": round(metrics["expected_return"], 5),
        "won": bool(won),
        "settlement": settlement,
        "profit_unit": round(odds - 1, 4) if won else -1.0,
    })
    return detail


def _test_start_date(matches, test_fraction):
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction harus di antara 0 dan 1.")
    dates = sorted(matches["date"].drop_duplicates().tolist())
    if len(dates) < 2:
        raise ValueError("Butuh minimal dua tanggal pertandingan untuk split.")
    split_index = min(
        max(int(len(dates) * (1 - test_fraction)), 1),
        len(dates) - 1,
    )
    return dates[split_index]


def run_backtest(matches, test_fraction=DEFAULT_TEST_FRACTION, test_start=None):
    if matches.empty:
        raise ValueError("Tidak ada pertandingan valid untuk diuji.")
    start_date = (
        pd.to_datetime(test_start, errors="raise")
        if test_start else _test_start_date(matches, test_fraction)
    )
    test_matches = matches.loc[matches["date"] >= start_date]
    if test_matches.empty:
        raise ValueError(f"Tidak ada pertandingan pada/setelah {start_date.date()}.")

    # Warm the online model only with rows strictly before the holdout. Then
    # forecast an entire date before updating it, excluding same-day results.
    model = WalkForwardModel()
    training_matches = matches.loc[matches["date"] < start_date]
    for row in training_matches.to_dict(orient="records"):
        model.update(row)

    detail_rows = []
    for _, day_matches in test_matches.groupby("date", sort=True):
        rows = day_matches.to_dict(orient="records")
        detail_rows.extend(_score_forecast(row, model) for row in rows)
        for row in rows:
            model.update(row)
    details = pd.DataFrame(detail_rows)
    forecast_rows = details.loc[details["model_over25_pct"].notna()]
    bet_rows = details.loc[details["pick"].ne("")]
    brier = (
        float(forecast_rows["brier_over25"].mean())
        if len(forecast_rows) else None
    )
    probabilities = (
        forecast_rows["model_over25_pct"].clip(1e-6, 100 - 1e-6) / 100
    )
    outcomes = (
        forecast_rows["actual_ou25"].eq("OVER").astype(float)
    )
    log_loss = (
        float((-(outcomes * probabilities.map(math.log)
                 + (1 - outcomes) * (1 - probabilities).map(math.log))).mean())
        if len(forecast_rows) else None
    )
    historical_base_rate = (
        float((training_matches["hg"] + training_matches["ag"] > 2.5).mean())
        if len(training_matches) else 0.5
    )
    baseline_brier = (
        float(((outcomes - historical_base_rate) ** 2).mean())
        if len(forecast_rows) else None
    )
    bet_count = len(bet_rows)
    net_profit = float(bet_rows["profit_unit"].sum()) if bet_count else 0.0
    summary = {
        "test_start": pd.Timestamp(test_matches["date"].min()).date().isoformat(),
        "test_end": pd.Timestamp(test_matches["date"].max()).date().isoformat(),
        "test_matches": len(test_matches),
        "model_forecasts": len(forecast_rows),
        "bets": bet_count,
        "wins": int(bet_rows["won"].sum()) if bet_count else 0,
        "losses": int(bet_count - bet_rows["won"].sum()) if bet_count else 0,
        "win_rate_pct": (
            float(bet_rows["won"].mean() * 100) if bet_count else None
        ),
        "net_profit_units": net_profit,
        "roi_pct": net_profit / bet_count * 100 if bet_count else None,
        "expected_roi_pct": (
            float(bet_rows["expected_profit_unit"].mean() * 100)
            if bet_count else None
        ),
        "brier_score_over25": brier,
        "historical_base_rate_over25_pct": historical_base_rate * 100,
        "historical_base_rate_brier": baseline_brier,
        "brier_skill_vs_historical_rate": (
            1 - brier / baseline_brier
            if brier is not None and baseline_brier else None
        ),
        "log_loss_over25": log_loss,
        "mean_absolute_calibration_error": _calibration_error(forecast_rows),
        "skip_reasons": dict(Counter(
            details.loc[details["pick"].eq("") & details["skip_reason"].ne(""), "skip_reason"]
        )),
        "details": details,
    }
    summary["breakdowns"] = build_breakdowns(details)
    return summary


def _calibration_error(forecast_rows):
    if forecast_rows.empty:
        return None
    bins = pd.cut(
        forecast_rows["model_over25_pct"] / 100,
        bins=[0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1],
        include_lowest=True,
    )
    grouped = forecast_rows.assign(_bin=bins).groupby(
        "_bin", observed=True
    )
    return float(sum(
        len(group) / len(forecast_rows)
        * abs(
            group["model_over25_pct"].mean() / 100
            - group["actual_ou25"].eq("OVER").mean()
        )
        for _, group in grouped
    ))


def _aggregate_rows(rows, group_type, group_value):
    forecast_rows = rows.loc[rows["model_over25_pct"].notna()]
    bets = rows.loc[rows["pick"].ne("")]
    count = len(bets)
    net = float(bets["profit_unit"].sum()) if count else 0.0
    return {
        "group_type": group_type,
        "group": group_value,
        "forecasts": len(forecast_rows),
        "bets": count,
        "wins": int(bets["won"].sum()) if count else 0,
        "win_rate_pct": float(bets["won"].mean() * 100) if count else None,
        "net_profit_units": net,
        "realized_roi_pct": net / count * 100 if count else None,
        "expected_roi_pct": (
            float(bets["expected_profit_unit"].mean() * 100) if count else None
        ),
        "brier_score_over25": (
            float(forecast_rows["brier_over25"].mean())
            if len(forecast_rows) else None
        ),
    }


def build_breakdowns(details):
    """Create per-line, odds, league, calibration, and gap-threshold diagnostics."""
    output = []
    candidates = details.loc[
        details["candidate_pick"].ne("")
        & details["candidate_expected_return"].notna()
        & details["candidate_odds"].between(MIN_OU_ODDS, MAX_OU_ODDS)
        & details["value_gap"].le(MAX_OU_GAP)
        & details["candidate_expected_return"].gt(0)
    ].copy()
    if not candidates.empty:
        candidates["pick_line"] = candidates["candidate_pick"].str.extract(
            r"(\d+(?:\.\d+)?)$"
        )[0].astype(float)
        for line, group in candidates.groupby("pick_line"):
            output.append(_aggregate_rows(group, "line", f"{line:g}"))

        def odds_band(odds):
            for low, high in ODDS_BANDS:
                if low <= odds < high or (high == MAX_OU_ODDS and odds <= high):
                    return f"{low:.2f}-{high:.2f}"
            return "di_luar_rentang"

        candidates["odds_band"] = candidates["candidate_odds"].map(odds_band)
        for band, group in candidates.groupby("odds_band"):
            output.append(_aggregate_rows(group, "rentang_odds", band))
        for league, group in candidates.groupby("league"):
            output.append(_aggregate_rows(group, "liga", league))

        for threshold in GAP_THRESHOLDS:
            selected = candidates.loc[candidates["value_gap"] >= threshold].copy()
            selected["pick"] = selected["candidate_pick"]
            selected["market_odds"] = selected["candidate_odds"]
            selected["expected_profit_unit"] = selected["candidate_expected_return"]
            selected["won"] = (
                selected["candidate_pick"].str.split().str[0]
                == selected["actual_ou25"]
            )
            selected["profit_unit"] = selected.apply(
                lambda row: (
                    row["candidate_odds"] - 1 if row["won"] else -1.0
                ),
                axis=1,
            )
            output.append(_aggregate_rows(
                selected, "batas_gap_pp", f">={threshold:g}"
            ))

    forecasts = details.loc[details["model_over25_pct"].notna()].copy()
    if not forecasts.empty:
        forecasts["probability_bin"] = pd.cut(
            forecasts["model_over25_pct"] / 100,
            bins=[0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1],
            include_lowest=True,
        )
        for bin_name, group in forecasts.groupby(
            "probability_bin", observed=True
        ):
            output.append({
                "group_type": "kalibrasi_probabilitas",
                "group": str(bin_name),
                "forecasts": len(group),
                "bets": None,
                "wins": None,
                "win_rate_pct": None,
                "net_profit_units": None,
                "realized_roi_pct": None,
                "expected_roi_pct": None,
                "mean_predicted_over_pct": float(
                    group["model_over25_pct"].mean()
                ),
                "actual_over_pct": float(
                    group["actual_ou25"].eq("OVER").mean() * 100
                ),
                "brier_score_over25": float(group["brier_over25"].mean()),
            })
    return pd.DataFrame(output)


def _print_percent(value):
    return "n/a" if value is None else f"{value:.2f}%"


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Backtest Poisson O/U 2.5 secara kronologis; "
            "fitur hanya memakai hasil dari tanggal sebelumnya."
        )
    )
    parser.add_argument(
        "--test-fraction", type=float, default=DEFAULT_TEST_FRACTION,
        help="Porsi tanggal terbaru untuk pengujian (default 0.20).",
    )
    parser.add_argument(
        "--test-start",
        help="Tanggal awal uji opsional (YYYY-MM-DD); mengesampingkan test-fraction.",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help=f"Lokasi CSV detail hasil (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--summary-output", default=DEFAULT_SUMMARY_OUTPUT,
        help=f"Lokasi CSV diagnosis (default: {DEFAULT_SUMMARY_OUTPUT}).",
    )
    args = parser.parse_args()

    try:
        matches = load_matches()
        summary = run_backtest(
            matches,
            test_fraction=args.test_fraction,
            test_start=args.test_start,
        )
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"❌ Backtest gagal: {exc}")
        return 1

    print("=" * 68)
    print("⚽ BACKTEST O/U 2.5 — WALK-FORWARD KRONOLOGIS")
    print("=" * 68)
    print(f"Holdout tanggal: {summary['test_start']} s/d {summary['test_end']}")
    print(
        "Model: form 10 kandang terakhir + 10 tandang terakhir, "
        "shot-on-target proxy, Poisson; H2H hanya koreksi 10%."
    )
    print(
        f"Aturan pick awal: gap no-vig +{MIN_OU_GAP:.0f} s/d "
        f"+{MAX_OU_GAP:.0f} pp; EV positif; odds "
        f"{MIN_OU_ODDS:.2f}–{MAX_OU_ODDS:.2f}"
    )
    print(
        f"Pertandingan uji: {summary['test_matches']:,} | "
        f"Forecast model valid: {summary['model_forecasts']:,} | "
        f"Pick taruhan: {summary['bets']:,}"
    )
    print(f"Win rate: {_print_percent(summary['win_rate_pct'])}")
    print(f"ROI aktual: {_print_percent(summary['roi_pct'])}")
    print(f"ROI ekspektasian model: {_print_percent(summary['expected_roi_pct'])}")
    print(f"Brier score O2.5: {summary['brier_score_over25']}")
    print(
        f"Brier rate historis train ({summary['historical_base_rate_over25_pct']:.2f}%): "
        f"{summary['historical_base_rate_brier']}"
    )
    print(
        f"Brier skill vs rate historis: "
        f"{summary['brier_skill_vs_historical_rate']}"
    )
    print(f"Log loss O2.5: {summary['log_loss_over25']}")
    print(
        "Rata-rata galat kalibrasi: "
        f"{_print_percent(summary['mean_absolute_calibration_error'] * 100) if summary['mean_absolute_calibration_error'] is not None else 'n/a'}"
    )
    print(f"Profit bersih: {summary['net_profit_units']:+.2f} unit")
    if summary["skip_reasons"]:
        print("Alasan dilewati:")
        for reason, count in sorted(summary["skip_reasons"].items()):
            print(f"  - {reason}: {count:,}")

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    summary["details"].to_csv(args.output, index=False)
    summary_dir = os.path.dirname(args.summary_output)
    if summary_dir:
        os.makedirs(summary_dir, exist_ok=True)
    summary["breakdowns"].to_csv(args.summary_output, index=False)
    print(f"\n💾 Detail per pertandingan: {args.output}")
    print(f"💾 Diagnosis line/odds/liga/gap/kalibrasi: {args.summary_output}")
    print(
        "\nCatatan: arsip historis hanya memiliki odds O/U 2.5 yang konsisten; "
        "Asian line diuji penuh pada prediksi aktif, belum pada arsip hasil. "
        "Gap +5 pp tetap ambang awal, bukan jaminan nilai atau ambang tervalidasi."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
