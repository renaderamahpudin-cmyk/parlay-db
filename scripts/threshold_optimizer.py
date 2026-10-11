"""Find optimal thresholds for O/U picks based on historical backtest ROI.

This script analyzes backtest results and recommends threshold adjustments
to maximize ROI while maintaining statistical significance.
"""
import argparse
from collections import defaultdict
import json
import os
import sys

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prediction_config import MAX_OU_GAP, MAX_OU_ODDS, MIN_OU_GAP, MIN_OU_ODDS


def load_backtest_results(csv_path):
    """Load the detailed backtest CSV."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Backtest results not found: {csv_path}")
    df = pd.read_csv(csv_path)
    return df


def filter_by_threshold(df, min_gap, max_gap, min_odds, max_odds, min_ev=0):
    """Filter backtest rows by threshold criteria."""
    filtered = df[
        (df["value_gap"] >= min_gap)
        & (df["value_gap"] <= max_gap)
        & (df["candidate_odds"] >= min_odds)
        & (df["candidate_odds"] <= max_odds)
        & (df["candidate_expected_return"] > min_ev)
        & (df["pick"].ne(""))
    ].copy()
    return filtered


def compute_roi_metrics(df_picks):
    """Compute ROI, win rate, and statistical metrics for a set of picks."""
    if df_picks.empty:
        return {
            "n_picks": 0,
            "n_wins": 0,
            "n_losses": 0,
            "win_rate_pct": None,
            "net_profit": 0.0,
            "roi_pct": None,
            "avg_odds": None,
            "avg_gap": None,
            "avg_ev": None,
            "stdev_profit": None,
            "sharpe_ratio": None,
        }

    n_picks = len(df_picks)
    n_wins = (df_picks["won"] == True).sum()
    n_losses = (df_picks["won"] == False).sum()
    net_profit = df_picks["profit_unit"].sum()
    win_rate = (n_wins / n_picks * 100) if n_picks > 0 else None
    roi = (net_profit / n_picks * 100) if n_picks > 0 else None

    avg_odds = df_picks["candidate_odds"].mean()
    avg_gap = df_picks["value_gap"].mean()
    avg_ev = df_picks["candidate_expected_return"].mean()

    profit_series = df_picks["profit_unit"]
    stdev = profit_series.std() if len(profit_series) > 1 else 0.0
    sharpe = (profit_series.mean() / stdev * np.sqrt(252)) if stdev > 0 else None

    return {
        "n_picks": n_picks,
        "n_wins": n_wins,
        "n_losses": n_losses,
        "win_rate_pct": round(win_rate, 2) if win_rate else None,
        "net_profit": round(net_profit, 2),
        "roi_pct": round(roi, 2) if roi else None,
        "avg_odds": round(avg_odds, 2),
        "avg_gap": round(avg_gap, 2),
        "avg_ev": round(avg_ev, 5),
        "stdev_profit": round(stdev, 3),
        "sharpe_ratio": round(sharpe, 3) if sharpe else None,
    }


def sweep_gap_threshold(df, gap_values, min_odds=MIN_OU_ODDS, max_odds=MAX_OU_ODDS):
    """Sweep different MIN_GAP values and compute ROI for each."""
    results = []
    for gap in gap_values:
        picks = filter_by_threshold(df, min_gap=gap, max_gap=MAX_OU_GAP, 
                                     min_odds=min_odds, max_odds=max_odds)
        metrics = compute_roi_metrics(picks)
        metrics["min_gap_threshold"] = gap
        results.append(metrics)
    return pd.DataFrame(results)


def sweep_odds_range(df, min_odds_values, gap=MIN_OU_GAP):
    """Sweep different MIN_ODDS values and compute ROI for each."""
    results = []
    for min_odds in min_odds_values:
        picks = filter_by_threshold(df, min_gap=gap, max_gap=MAX_OU_GAP,
                                     min_odds=min_odds, max_odds=MAX_OU_ODDS)
        metrics = compute_roi_metrics(picks)
        metrics["min_odds_threshold"] = round(min_odds, 2)
        results.append(metrics)
    return pd.DataFrame(results)


def sweep_max_gap(df, max_gap_values, min_gap=MIN_OU_GAP, min_odds=MIN_OU_ODDS):
    """Sweep different MAX_GAP values and compute ROI for each."""
    results = []
    for max_gap in max_gap_values:
        picks = filter_by_threshold(df, min_gap=min_gap, max_gap=max_gap,
                                     min_odds=min_odds, max_odds=MAX_OU_ODDS)
        metrics = compute_roi_metrics(picks)
        metrics["max_gap_threshold"] = max_gap
        results.append(metrics)
    return pd.DataFrame(results)


def analyze_by_league(df, min_gap=MIN_OU_GAP):
    """Analyze ROI by league."""
    picks = filter_by_threshold(df, min_gap=min_gap, max_gap=MAX_OU_GAP,
                                 min_odds=MIN_OU_ODDS, max_odds=MAX_OU_ODDS)
    if picks.empty:
        return pd.DataFrame()

    results = []
    for league, group in picks.groupby("league"):
        metrics = compute_roi_metrics(group)
        metrics["league"] = league
        results.append(metrics)
    return pd.DataFrame(results).sort_values("roi_pct", ascending=False, na_position="last")


def analyze_by_odds_band(df, min_gap=MIN_OU_GAP):
    """Analyze ROI by odds bands."""
    picks = filter_by_threshold(df, min_gap=min_gap, max_gap=MAX_OU_GAP,
                                 min_odds=MIN_OU_ODDS, max_odds=MAX_OU_ODDS)
    if picks.empty:
        return pd.DataFrame()

    odds_bands = [
        (1.2, 1.5, "1.20-1.50"),
        (1.5, 1.8, "1.50-1.80"),
        (1.8, 2.1, "1.80-2.10"),
        (2.1, 2.5, "2.10-2.50"),
        (2.5, 4.0, "2.50-4.00"),
    ]

    results = []
    for low, high, label in odds_bands:
        group = picks[(picks["candidate_odds"] >= low) & (picks["candidate_odds"] < high)]
        metrics = compute_roi_metrics(group)
        metrics["odds_band"] = label
        results.append(metrics)
    return pd.DataFrame(results)


def analyze_calibration(df, min_gap=MIN_OU_GAP):
    """Analyze calibration: predicted vs actual probability."""
    picks = filter_by_threshold(df, min_gap=min_gap, max_gap=MAX_OU_GAP,
                                 min_odds=MIN_OU_ODDS, max_odds=MAX_OU_ODDS)
    if picks.empty:
        return pd.DataFrame()

    # Bin by predicted confidence
    bins = [0, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 101]
    picks["conf_bin"] = pd.cut(picks["pick_conf"], bins=bins, right=False)

    results = []
    for bin_label, group in picks.groupby("conf_bin", observed=True):
        if group.empty:
            continue
        actual_win_rate = (group["won"] == True).sum() / len(group) * 100
        predicted_conf = group["pick_conf"].mean()
        metrics = compute_roi_metrics(group)
        metrics["confidence_bin"] = str(bin_label)
        metrics["predicted_confidence"] = round(predicted_conf, 1)
        metrics["actual_win_rate"] = round(actual_win_rate, 1)
        metrics["calibration_error"] = round(abs(predicted_conf - actual_win_rate), 1)
        results.append(metrics)
    return pd.DataFrame(results)


def recommend_thresholds(df):
    """Recommend optimal thresholds based on ROI analysis."""
    recommendations = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "analysis": {},
    }

    print("\\n" + "=" * 70)
    print("SWEEPING MIN_GAP THRESHOLD")
    print("=" * 70)
    gap_sweep = sweep_gap_threshold(df, np.arange(0, 35, 2.5))
    print(gap_sweep.to_string(index=False))
    best_gap_idx = gap_sweep["roi_pct"].idxmax() if gap_sweep["roi_pct"].notna().any() else 0
    best_gap_row = gap_sweep.iloc[best_gap_idx]
    recommendations["analysis"]["gap_sweep"] = gap_sweep.to_dict(orient="records")
    recommendations["best_min_gap"] = {
        "threshold": float(best_gap_row["min_gap_threshold"]),
        "n_picks": int(best_gap_row["n_picks"]),
        "roi_pct": float(best_gap_row["roi_pct"]) if pd.notna(best_gap_row["roi_pct"]) else None,
        "win_rate_pct": float(best_gap_row["win_rate_pct"]) if pd.notna(best_gap_row["win_rate_pct"]) else None,
    }
    print(f"\\n✅ RECOMMENDED MIN_GAP: {best_gap_row['min_gap_threshold']:.1f} pp")
    print(f"   N picks: {best_gap_row['n_picks']}, ROI: {best_gap_row['roi_pct']:.2f}%, Win: {best_gap_row['win_rate_pct']:.1f}%\\n")

    print("\\n" + "=" * 70)
    print("SWEEPING MIN_ODDS THRESHOLD")
    print("=" * 70)
    odds_sweep = sweep_odds_range(df, np.arange(1.2, 3.0, 0.1))
    print(odds_sweep.to_string(index=False))
    best_odds_idx = odds_sweep["roi_pct"].idxmax() if odds_sweep["roi_pct"].notna().any() else 0
    best_odds_row = odds_sweep.iloc[best_odds_idx]
    recommendations["analysis"]["odds_sweep"] = odds_sweep.to_dict(orient="records")
    recommendations["best_min_odds"] = {
        "threshold": float(best_odds_row["min_odds_threshold"]),
        "n_picks": int(best_odds_row["n_picks"]),
        "roi_pct": float(best_odds_row["roi_pct"]) if pd.notna(best_odds_row["roi_pct"]) else None,
        "win_rate_pct": float(best_odds_row["win_rate_pct"]) if pd.notna(best_odds_row["win_rate_pct"]) else None,
    }
    print(f"\\n✅ RECOMMENDED MIN_ODDS: {best_odds_row['min_odds_threshold']:.2f}")
    print(f"   N picks: {best_odds_row['n_picks']}, ROI: {best_odds_row['roi_pct']:.2f}%, Win: {best_odds_row['win_rate_pct']:.1f}%\\n")

    print("\\n" + "=" * 70)
    print("SWEEPING MAX_GAP THRESHOLD")
    print("=" * 70)
    max_gap_sweep = sweep_max_gap(df, np.arange(15, 50, 5))
    print(max_gap_sweep.to_string(index=False))
    best_max_gap_idx = max_gap_sweep["roi_pct"].idxmax() if max_gap_sweep["roi_pct"].notna().any() else 0
    best_max_gap_row = max_gap_sweep.iloc[best_max_gap_idx]
    recommendations["analysis"]["max_gap_sweep"] = max_gap_sweep.to_dict(orient="records")
    recommendations["best_max_gap"] = {
        "threshold": float(best_max_gap_row["max_gap_threshold"]),
        "n_picks": int(best_max_gap_row["n_picks"]),
        "roi_pct": float(best_max_gap_row["roi_pct"]) if pd.notna(best_max_gap_row["roi_pct"]) else None,
        "win_rate_pct": float(best_max_gap_row["win_rate_pct"]) if pd.notna(best_max_gap_row["win_rate_pct"]) else None,
    }
    print(f"\\n✅ RECOMMENDED MAX_GAP: {best_max_gap_row['max_gap_threshold']:.1f} pp")
    print(f"   N picks: {best_max_gap_row['n_picks']}, ROI: {best_max_gap_row['roi_pct']:.2f}%, Win: {best_max_gap_row['win_rate_pct']:.1f}%\\n")

    print("\\n" + "=" * 70)
    print("BREAKDOWN BY LEAGUE")
    print("=" * 70)
    league_analysis = analyze_by_league(df)
    if not league_analysis.empty:
        print(league_analysis.to_string(index=False))
        recommendations["analysis"]["by_league"] = league_analysis.to_dict(orient="records")

    print("\\n" + "=" * 70)
    print("BREAKDOWN BY ODDS BAND")
    print("=" * 70)
    odds_band_analysis = analyze_by_odds_band(df)
    if not odds_band_analysis.empty:
        print(odds_band_analysis.to_string(index=False))
        recommendations["analysis"]["by_odds_band"] = odds_band_analysis.to_dict(orient="records")

    print("\\n" + "=" * 70)
    print("CALIBRATION ANALYSIS")
    print("=" * 70)
    calibration = analyze_calibration(df)
    if not calibration.empty:
        print(calibration.to_string(index=False))
        recommendations["analysis"]["calibration"] = calibration.to_dict(orient="records")
        mean_cal_error = calibration["calibration_error"].mean()
        print(f"\\n📊 Mean calibration error: {mean_cal_error:.1f} pp")

    return recommendations


def main():
    parser = argparse.ArgumentParser(
        description="Optimize O/U prediction thresholds based on backtest ROI."
    )
    parser.add_argument(
        "--backtest-csv",
        default="generated-artifacts/backtest_ou_poisson_walkforward.csv",
        help="Path to backtest results CSV.",
    )
    parser.add_argument(
        "--output",
        default="generated-artifacts/threshold_recommendations.json",
        help="Path to save threshold recommendations.",
    )
    args = parser.parse_args()

    try:
        df = load_backtest_results(args.backtest_csv)
        print(f"\\n✅ Loaded {len(df):,} backtest records")
        print(f"   Picks made: {(df['pick'].ne('').sum()):,}")
        print(f"   Overall win rate: {(df['won'] == True).sum() / (df['pick'].ne('').sum()) * 100:.2f}%")
        print(f"   Overall ROI: {(df[df['pick'].ne('')]['profit_unit'].sum() / df['pick'].ne('').sum() * 100):.2f}%")

        recommendations = recommend_thresholds(df)

        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)
        print(f"\\n💾 Recommendations saved: {args.output}")

        print("\\n" + "=" * 70)
        print("SUGGESTED CONFIGURATION (prediction_config.py)")
        print("=" * 70)
        print(f"MIN_OU_GAP = {recommendations['best_min_gap']['threshold']}")
        print(f"MAX_OU_GAP = {recommendations['best_max_gap']['threshold']}")
        print(f"MIN_OU_ODDS = {recommendations['best_min_odds']['threshold']}")
        print()

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
