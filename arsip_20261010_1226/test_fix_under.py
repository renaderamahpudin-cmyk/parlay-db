"""
TEST FIX: Under + Push
"""
import sys
sys.path.insert(0, "scripts")
from parlay_builder_v3 import bandingkan_opsi_2

# Test case Wieczysta vs Wisla (3-0, total 3 gol)
# Data dummy 20 match dengan distribusi serupa
gol_pairs = [
    (3,0), (2,1), (1,1), (0,1), (3,0), (2,2), (1,0), (3,1), (0,0), (2,0),
    (1,1), (3,0), (2,1), (1,0), (0,2), (2,1), (3,0), (1,1), (0,1), (2,0),
]

ou_lines = [
    {"line": 2.5, "over": 1.65, "under": 2.33},
    {"line": 3.0, "over": 2.06, "under": 1.84},
    {"line": 3.5, "over": 2.07, "under": 1.83},
    {"line": 3.75, "over": 1.65, "under": 2.33},
]

top_1x2, top_ou, titik = bandingkan_opsi_2(
    gol_pairs=gol_pairs,
    ou_lines=ou_lines,
    odds_home=1.29,
    odds_draw=5.68,
    odds_away=8.68,
    home_win_rate=37.5,
    away_win_rate=45.0,
    draw_rate=17.5,
)

print("=" * 60)
print("📊 TEST FIX UNDER + PUSH")
print("=" * 60)

# Analisa manual
total_gols = [g[0] + g[1] for g in gol_pairs]
n = len(total_gols)

print(f"\nTotal match: {n}")
print(f"Total gol sample: {total_gols}")

# Per line
for line in [2.5, 3.0, 3.5, 3.75]:
    over = sum(1 for g in total_gols if g > line)
    under = sum(1 for g in total_gols if g < line)
    push = sum(1 for g in total_gols if g == line)
    print(f"\nLine {line}:")
    print(f"  Over (>):  {over}/{n} = {over/n*100:.1f}%")
    print(f"  Under (<): {under}/{n} = {under/n*100:.1f}%")
    if push > 0:
        print(f"  Push (=):  {push}/{n} = {push/n*100:.1f}%")
    print(f"  Total: {(over+under+push)/n*100:.1f}%")

print(f"\n{'='*60}")
if top_ou:
    print(f"🎯 TOP PICK: {top_ou['pick']}")
    print(f"   Odds: {top_ou['odds']}")
    print(f"   Prob: {top_ou['prob']}%")
    print(f"   Gap: {top_ou['gap']:+.1f}%")
print(f"{'='*60}")
