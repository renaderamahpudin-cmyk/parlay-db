"""Chronological walk-forward backtest for the current O/U 2.5 baseline."""
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


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

DATA_FILE = "data/football_data/all_football_data.csv"
DEFAULT_OUTPUT = "output/backtest_ou_walkforward.csv"
MIN_H2H = 5
DEFAULT_TEST_FRACTION = 0.20
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


def evaluate_fixture(row, history_index, min_h2h=MIN_H2H):
    """Evaluate one O/U 2.5 fixture using only pair results before its date."""
    h2h_count, h2h_over_count = history_summary_before(
        history_index, row["home_key"], row["away_key"], row["date"]
    )
    actual_over = int(row["hg"] + row["ag"] > 2.5)
    detail = {
        "date": pd.Timestamp(row["date"]).date().isoformat(),
        "league": row["league"],
        "home": row["home"],
        "away": row["away"],
        "h2h_before": h2h_count,
        "model_over25_pct": None,
        "brier_over25": None,
        "actual_total": int(row["hg"] + row["ag"]),
        "actual_ou25": "OVER" if actual_over else "UNDER",
        "pick": "",
        "pick_conf": None,
        "market_odds": None,
        "market_source": "",
        "market_implied_raw": None,
        "market_overround_pct": None,
        "value_gap": None,
        "expected_profit_unit": None,
        "won": None,
        "profit_unit": None,
        "skip_reason": "",
    }
    if h2h_count < min_h2h:
        detail["skip_reason"] = "h2h_kurang_dari_minimum"
        return detail

    model_over_probability = h2h_over_count / h2h_count
    detail["model_over25_pct"] = round(model_over_probability * 100, 1)
    detail["brier_over25"] = (model_over_probability - actual_over) ** 2

    prices = market_odds(row)
    if prices is None:
        detail["skip_reason"] = "odds_ou_tidak_tersedia"
        return detail

    market_source, odds_over, odds_under = prices
    detail["market_source"] = market_source
    detail["market_overround_pct"] = round(
        ((1 / odds_over) + (1 / odds_under) - 1) * 100, 2
    )
    options = [
        {
            "pick": "OVER 2.5",
            "probability": model_over_probability,
            "odds": odds_over,
        },
        {
            "pick": "UNDER 2.5",
            "probability": 1 - model_over_probability,
            "odds": odds_under,
        },
    ]
    for option in options:
        option["implied"] = 1 / option["odds"]
        option["gap"] = (option["probability"] - option["implied"]) * 100

    best = max(options, key=lambda option: option["gap"])
    detail["market_implied_raw"] = round(best["implied"] * 100, 1)
    detail["value_gap"] = round(best["gap"], 1)
    if best["gap"] < MIN_OU_GAP:
        detail["skip_reason"] = "gap_di_bawah_minimum"
        return detail
    if best["gap"] > MAX_OU_GAP:
        detail["skip_reason"] = "gap_di_atas_batas_wajar"
        return detail
    if not MIN_OU_ODDS <= best["odds"] <= MAX_OU_ODDS:
        detail["skip_reason"] = "odds_di_luar_batas"
        return detail

    won = (best["pick"] == "OVER 2.5" and actual_over) or (
        best["pick"] == "UNDER 2.5" and not actual_over
    )
    detail.update({
        "pick": best["pick"],
        "pick_conf": round(best["probability"] * 100, 1),
        "market_odds": round(best["odds"], 2),
        "expected_profit_unit": round(best["probability"] * best["odds"] - 1, 4),
        "won": bool(won),
        "profit_unit": round(best["odds"] - 1, 4) if won else -1.0,
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

    # The index includes the full archive intentionally; every query uses bisect_left
    # so same-day and future results cannot enter a fixture's historical sample.
    history_index = build_h2h_index(matches)
    details = pd.DataFrame([
        evaluate_fixture(row, history_index)
        for row in test_matches.to_dict(orient="records")
    ])
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
    bet_count = len(bet_rows)
    net_profit = float(bet_rows["profit_unit"].sum()) if bet_count else 0.0
    summary = {
        "test_start": pd.Timestamp(test_matches["date"].min()).date().isoformat(),
        "test_end": pd.Timestamp(test_matches["date"].max()).date().isoformat(),
        "test_matches": len(test_matches),
        "h2h_forecasts": len(forecast_rows),
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
        "log_loss_over25": log_loss,
        "skip_reasons": dict(Counter(
            details.loc[details["pick"].eq("") & details["skip_reason"].ne(""), "skip_reason"]
        )),
        "details": details,
    }
    return summary


def _print_percent(value):
    return "n/a" if value is None else f"{value:.2f}%"


def main():
    parser = argparse.ArgumentParser(
        description="Backtest O/U 2.5 secara kronologis tanpa data masa depan."
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
        f"Aturan: H2H sebelum tanggal laga, minimum {MIN_H2H}; "
        f"gap +{MIN_OU_GAP:.0f} s/d +{MAX_OU_GAP:.0f} pp; "
        f"odds {MIN_OU_ODDS:.2f}–{MAX_OU_ODDS:.2f}"
    )
    print(
        f"Pertandingan uji: {summary['test_matches']:,} | "
        f"Forecast H2H valid: {summary['h2h_forecasts']:,} | "
        f"Pick taruhan: {summary['bets']:,}"
    )
    print(f"Win rate: {_print_percent(summary['win_rate_pct'])}")
    print(f"ROI aktual: {_print_percent(summary['roi_pct'])}")
    print(f"ROI ekspektasian model: {_print_percent(summary['expected_roi_pct'])}")
    print(f"Brier score O2.5: {summary['brier_score_over25']}")
    print(f"Log loss O2.5: {summary['log_loss_over25']}")
    print(f"Profit bersih: {summary['net_profit_units']:+.2f} unit")
    if summary["skip_reasons"]:
        print("Alasan dilewati:")
        for reason, count in sorted(summary["skip_reasons"].items()):
            print(f"  - {reason}: {count:,}")

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    summary["details"].to_csv(args.output, index=False)
    print(f"\n💾 Detail backtest disimpan: {args.output}")
    print(
        "\nCatatan: ini baseline H2H O/U 2.5 dengan odds arsip; "
        "hasil bukan jaminan prediksi dan belum menguji line O/U lain."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
