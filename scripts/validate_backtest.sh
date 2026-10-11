#!/bin/bash
# Quick validation script untuk backtest results

echo "======================================================================"
echo "🔍 ANALISIS HASIL BACKTEST"
echo "======================================================================"

python3 << 'EOF'
import pandas as pd
import sys

csv_path = "generated-artifacts/backtest_ou_poisson_walkforward.csv"

try:
    df = pd.read_csv(csv_path)
    print(f"\n📊 Total records: {len(df):,}")
    
    # Filter untuk picks yang benar-benar di-pick
    picks = df[df["pick"].ne("")].copy()
    print(f"📊 Actual picks made: {len(picks):,}")
    
    if len(picks) == 0:
        print("❌ No picks made!")
        sys.exit(1)
    
    # Metrics
    wins = (picks["won"] == True).sum()
    losses = (picks["won"] == False).sum()
    win_rate = wins / len(picks) * 100
    net_profit = picks["profit_unit"].sum()
    roi = net_profit / len(picks) * 100
    
    print(f"\n💰 Hasil Nyata:")
    print(f"   Wins: {wins:,} ({win_rate:.2f}%)")
    print(f"   Losses: {losses:,}")
    print(f"   Net Profit: {net_profit:+.2f} unit")
    print(f"   ROI: {roi:+.2f}%")
    
    # Expected vs Actual
    expected_roi = picks["expected_profit_unit"].mean() * 100
    print(f"\n⚠️  Model Expectation: {expected_roi:+.2f}%")
    print(f"❌ Gap: {roi - expected_roi:+.2f} pp (model terlalu optimistic!)")
    
    # Gap analysis
    print(f"\n📈 Pick Distribution by Gap:")
    gap_ranges = [
        (0, 5),
        (5, 10),
        (10, 15),
        (15, 20),
        (20, 25),
        (25, 35)
    ]
    
    for gap_min, gap_max in gap_ranges:
        subset = picks[(picks["value_gap"] >= gap_min) & (picks["value_gap"] < gap_max)]
        if len(subset) > 0:
            subset_roi = subset["profit_unit"].sum() / len(subset) * 100
            subset_wr = (subset["won"] == True).sum() / len(subset) * 100
            print(f"   Gap {gap_min:2d}-{gap_max:2d} pp: {len(subset):5d} picks, ROI {subset_roi:6.2f}%, WR {subset_wr:5.1f}%")
    
    # Odds analysis
    print(f"\n📊 Pick Distribution by Odds:")
    odds_ranges = [
        (1.2, 1.5),
        (1.5, 1.8),
        (1.8, 2.1),
        (2.1, 2.5),
        (2.5, 4.0)
    ]
    
    for odds_min, odds_max in odds_ranges:
        subset = picks[(picks["candidate_odds"] >= odds_min) & (picks["candidate_odds"] < odds_max)]
        if len(subset) > 0:
            subset_roi = subset["profit_unit"].sum() / len(subset) * 100
            subset_wr = (subset["won"] == True).sum() / len(subset) * 100
            print(f"   Odds {odds_min:.2f}-{odds_max:.2f}: {len(subset):5d} picks, ROI {subset_roi:6.2f}%, WR {subset_wr:5.1f}%")
    
    # Recommendation
    print(f"\n🎯 REKOMENDASI:")
    
    # Cari gap dengan ROI terbaik
    best_gap_range = None
    best_gap_roi = float('-inf')
    for gap_min, gap_max in gap_ranges:
        subset = picks[(picks["value_gap"] >= gap_min) & (picks["value_gap"] < gap_max)]
        if len(subset) > 50:  # Minimal 50 picks untuk valid
            subset_roi = subset["profit_unit"].sum() / len(subset) * 100
            if subset_roi > best_gap_roi:
                best_gap_roi = subset_roi
                best_gap_range = (gap_min, gap_max)
    
    if best_gap_range and best_gap_roi > 0:
        print(f"   ✅ Gap {best_gap_range[0]}-{best_gap_range[1]} pp punya ROI terbaik: {best_gap_roi:.2f}%")
        print(f"   Rekomendasi: MIN_OU_GAP = {best_gap_range[0]}, MAX_OU_GAP = {best_gap_range[1]}")
    else:
        print(f"   ❌ Semua gap range punya ROI negatif")
        print(f"   Rekomendasi: NAIKKAN MIN_GAP drastis (ke 12-15)")
        print(f"   atau TURUNKAN MAX_GAP (ke 15-18)")
    
    print()
    
except FileNotFoundError:
    print(f"❌ File not found: {csv_path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

EOF
