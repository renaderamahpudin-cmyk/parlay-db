"""Complete automated tuning pipeline for O/U prediction thresholds.

This script runs backtest → optimizer → recommendation → update config
in a single automated workflow.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

import pandas as pd


def run_command(cmd, description):
    """Run shell command and report status."""
    print(f"\n{'='*70}")
    print(f"▶️  {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if result.returncode != 0:
        print(f"\n❌ FAILED: {description}")
        return False
    print(f"\n✅ SUCCESS: {description}")
    return True


def load_recommendations(json_path):
    """Load threshold recommendations from optimizer output."""
    if not os.path.exists(json_path):
        print(f"❌ Recommendations file not found: {json_path}")
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def select_best_threshold(recommendations):
    """Select best threshold based on ROI, win rate, and pick count."""
    if not recommendations or "analysis" not in recommendations:
        return None
    
    analysis = recommendations.get("analysis", {})
    
    best_gap = recommendations.get("best_min_gap", {})
    best_odds = recommendations.get("best_min_odds", {})
    best_max_gap = recommendations.get("best_max_gap", {})
    
    print("\n" + "="*70)
    print("ANALYSIS OF BEST THRESHOLDS")
    print("="*70)
    
    print("\n🎯 BEST MIN_GAP THRESHOLD:")
    print(f"   Threshold: {best_gap.get('threshold', 'N/A')}")
    print(f"   N picks: {best_gap.get('n_picks', 'N/A')}")
    print(f"   ROI: {best_gap.get('roi_pct', 'N/A')}%")
    print(f"   Win rate: {best_gap.get('win_rate_pct', 'N/A')}%")
    
    print("\n🎯 BEST MIN_ODDS THRESHOLD:")
    print(f"   Threshold: {best_odds.get('threshold', 'N/A')}")
    print(f"   N picks: {best_odds.get('n_picks', 'N/A')}")
    print(f"   ROI: {best_odds.get('roi_pct', 'N/A')}%")
    print(f"   Win rate: {best_odds.get('win_rate_pct', 'N/A')}%")
    
    print("\n🎯 BEST MAX_GAP THRESHOLD:")
    print(f"   Threshold: {best_max_gap.get('threshold', 'N/A')}")
    print(f"   N picks: {best_max_gap.get('n_picks', 'N/A')}")
    print(f"   ROI: {best_max_gap.get('roi_pct', 'N/A')}%")
    print(f"   Win rate: {best_max_gap.get('win_rate_pct', 'N/A')}%")
    
    return {
        "min_gap": best_gap.get("threshold"),
        "min_odds": best_odds.get("threshold"),
        "max_gap": best_max_gap.get("threshold"),
    }


def analyze_by_league(recommendations):
    """Show league-by-league performance."""
    if not recommendations or "analysis" not in recommendations:
        return
    
    by_league = recommendations.get("analysis", {}).get("by_league", [])
    if not by_league:
        return
    
    print("\n" + "="*70)
    print("LEAGUE-BY-LEAGUE PERFORMANCE")
    print("="*70)
    
    df = pd.DataFrame(by_league)
    df = df.sort_values("roi_pct", ascending=False, na_position="last")
    print(df[["league", "n_picks", "roi_pct", "win_rate_pct"]].to_string(index=False))
    
    profitable_leagues = df[df["roi_pct"] > 0]["league"].tolist()
    print(f"\n✅ Profitable leagues: {', '.join(profitable_leagues) if profitable_leagues else 'None'}")


def analyze_calibration(recommendations):
    """Show calibration analysis (predicted vs actual)."""
    if not recommendations or "analysis" not in recommendations:
        return
    
    calibration = recommendations.get("analysis", {}).get("calibration", [])
    if not calibration:
        return
    
    print("\n" + "="*70)
    print("CALIBRATION ANALYSIS (Predicted vs Actual)")
    print("="*70)
    
    df = pd.DataFrame(calibration)
    print(df[["confidence_bin", "predicted_confidence", "actual_win_rate", "calibration_error"]].to_string(index=False))
    
    mean_cal_error = df["calibration_error"].mean()
    print(f"\n📊 Mean calibration error: {mean_cal_error:.1f} pp")
    if mean_cal_error < 5:
        print("✅ Model calibration is GOOD (error < 5 pp)")
    elif mean_cal_error < 10:
        print("⚠️  Model calibration is OK (error 5-10 pp)")
    else:
        print("❌ Model calibration needs improvement (error > 10 pp)")


def update_config_file(thresholds):
    """Update prediction_config.py with new thresholds."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scripts/prediction_config.py"
    )
    
    if not thresholds:
        print(f"⚠️  No thresholds to update")
        return False
    
    min_gap = thresholds.get("min_gap", 5.0)
    max_gap = thresholds.get("max_gap", 20.0)
    min_odds = thresholds.get("min_odds", 1.20)
    
    new_content = f'''"""Stable prediction configuration for O/U pricing and filters."""

MIN_OU_GAP = {min_gap}
MAX_OU_GAP = {max_gap}
MIN_OU_ODDS = {min_odds}
MAX_OU_ODDS = 4.00

RECENT_MATCHES = 10
MIN_FORM_MATCHES = 5
H2H_WEIGHT = 0.10
PRIOR_MATCHES = 5

MIN_LAMBDA = 0.08
MAX_LAMBDA = 4.0
'''
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"\n✅ Updated {config_path}")
        print(f"   MIN_OU_GAP = {min_gap}")
        print(f"   MAX_OU_GAP = {max_gap}")
        print(f"   MIN_OU_ODDS = {min_odds}")
        return True
    except Exception as e:
        print(f"❌ Failed to update config: {e}")
        return False


def save_tuning_report(recommendations, output_path):
    """Save a human-readable tuning report."""
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = f"""# O/U Prediction Model Tuning Report
Generated: {datetime.now().isoformat()}

## Recommendations

### Best MIN_GAP Threshold
- Threshold: {recommendations.get('best_min_gap', {}).get('threshold', 'N/A')}
- N Picks: {recommendations.get('best_min_gap', {}).get('n_picks', 'N/A')}
- ROI: {recommendations.get('best_min_gap', {}).get('roi_pct', 'N/A')}%
- Win Rate: {recommendations.get('best_min_gap', {}).get('win_rate_pct', 'N/A')}%

### Best MIN_ODDS Threshold
- Threshold: {recommendations.get('best_min_odds', {}).get('threshold', 'N/A')}
- N Picks: {recommendations.get('best_min_odds', {}).get('n_picks', 'N/A')}
- ROI: {recommendations.get('best_min_odds', {}).get('roi_pct', 'N/A')}%
- Win Rate: {recommendations.get('best_min_odds', {}).get('win_rate_pct', 'N/A')}%

### Best MAX_GAP Threshold
- Threshold: {recommendations.get('best_max_gap', {}).get('threshold', 'N/A')}
- N Picks: {recommendations.get('best_max_gap', {}).get('n_picks', 'N/A')}
- ROI: {recommendations.get('best_max_gap', {}).get('roi_pct', 'N/A')}%
- Win Rate: {recommendations.get('best_max_gap', {}).get('win_rate_pct', 'N/A')}%

## How to Apply These Recommendations

1. Review the thresholds above
2. Update `scripts/prediction_config.py` with the recommended values
3. Run backtest again to validate the new thresholds
4. Monitor future predictions to ensure consistency

## Key Metrics to Monitor

- ROI: Should be positive over time
- Win Rate: Should be >= 50% with sufficient picks
- Calibration Error: Should be < 10 pp (percentage points)
- Profit Stability: Watch for consistent profitability across leagues

## Next Steps

1. If ROI is positive and stable: Deploy these thresholds
2. If ROI is negative: Review the sweep analysis and select more conservative thresholds
3. If calibration error is high: The model may need recalibration

For detailed analysis, see: generated-artifacts/threshold_recommendations.json
"""
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n💾 Saved tuning report: {output_path}")
    except Exception as e:
        print(f"⚠️  Failed to save report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Complete automated tuning pipeline for O/U prediction thresholds."
    )
    parser.add_argument(
        "--skip-backtest",
        action="store_true",
        help="Skip backtest and use existing results."
    )
    parser.add_argument(
        "--skip-optimizer",
        action="store_true",
        help="Skip optimizer and use existing recommendations."
    )
    parser.add_argument(
        "--auto-update-config",
        action="store_true",
        help="Automatically update prediction_config.py with best thresholds."
    )
    parser.add_argument(
        "--backtest-csv",
        default="generated-artifacts/backtest_ou_poisson_walkforward.csv",
        help="Path to backtest results CSV."
    )
    parser.add_argument(
        "--recommendations-json",
        default="generated-artifacts/threshold_recommendations.json",
        help="Path to threshold recommendations JSON."
    )
    parser.add_argument(
        "--report-output",
        default="generated-artifacts/tuning_report.md",
        help="Path to save tuning report."
    )
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🎯 AUTOMATED O/U PREDICTION TUNING PIPELINE")
    print("="*70)

    # Step 1: Backtest
    if not args.skip_backtest:
        backtest_cmd = [
            sys.executable,
            "scripts/backtest_ou_walkforward.py",
            "--output", args.backtest_csv,
        ]
        if not run_command(backtest_cmd, "Step 1/3: Running Backtest"):
            return 1
    else:
        print(f"\n⏭️  Skipping backtest (using {args.backtest_csv})")

    # Step 2: Optimize thresholds
    if not args.skip_optimizer:
        optimizer_cmd = [
            sys.executable,
            "scripts/threshold_optimizer.py",
            "--backtest-csv", args.backtest_csv,
            "--output", args.recommendations_json,
        ]
        if not run_command(optimizer_cmd, "Step 2/3: Optimizing Thresholds"):
            return 1
    else:
        print(f"\n⏭️  Skipping optimizer (using {args.recommendations_json})")

    # Step 3: Analyze and report
    print(f"\n{'='*70}")
    print("Step 3/3: Analyzing Results")
    print(f"{'='*70}")

    recommendations = load_recommendations(args.recommendations_json)
    if not recommendations:
        return 1

    best_thresholds = select_best_threshold(recommendations)
    analyze_by_league(recommendations)
    analyze_calibration(recommendations)

    # Step 4: Save report
    save_tuning_report(recommendations, args.report_output)

    # Step 5: Optional config update
    if args.auto_update_config and best_thresholds:
        print(f"\n{'='*70}")
        print("Step 4/4: Updating Configuration")
        print(f"{'='*70}")
        if update_config_file(best_thresholds):
            print("\n✅ Configuration updated successfully!")
            print("\n💡 Next steps:")
            print("   1. Commit changes to Git")
            print("   2. Run backtest again to verify new thresholds")
            print("   3. Monitor predictions in production")
        else:
            print("\n⚠️  Config update failed. Please manually update scripts/prediction_config.py")
    else:
        if best_thresholds:
            print(f"\n{'='*70}")
            print("📋 RECOMMENDED CONFIGURATION")
            print(f"{'='*70}")
            print(f"MIN_OU_GAP = {best_thresholds.get('min_gap', 5.0)}")
            print(f"MAX_OU_GAP = {best_thresholds.get('max_gap', 20.0)}")
            print(f"MIN_OU_ODDS = {best_thresholds.get('min_odds', 1.20)}")
            print("\n💡 To auto-apply: run with --auto-update-config flag")

    print(f"\n{'='*70}")
    print("✅ TUNING PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 Results saved to:")
    print(f"   - {args.backtest_csv}")
    print(f"   - {args.recommendations_json}")
    print(f"   - {args.report_output}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
