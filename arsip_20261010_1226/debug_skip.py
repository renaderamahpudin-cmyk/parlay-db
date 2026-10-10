"""
DEBUG 9 MATCH ENGLISH — Kenapa SKIP padahal H2H cukup?
"""
import json
import sys
sys.path.insert(0, "scripts")
from parlay_builder_v3 import cari_h2h, analisa, MIN_H2H, MIN_CONF_PICK
import pandas as pd

# Load match
with open("output/match_full.json") as f:
    matches = json.load(f)

# Filter English dengan H2H ada (skip yang H2H < 5)
english = [m for m in matches if "ENGLISH" in m["liga"].upper() or "ENGLAND" in m["liga"].upper()]

# Load DB
df1 = pd.read_csv("data/football_data/all_football_data.csv", low_memory=False)
df1 = df1.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
df1 = df1[["HomeTeam", "AwayTeam", "FTHG", "FTAG"]].copy()
df1.columns = ["home", "away", "hg", "ag"]

df2 = pd.read_csv("data/football_data_extra/all_extra.csv", low_memory=False)
df2 = df2.dropna(subset=["Home", "Away", "HG", "AG"])
df2 = df2[["Home", "Away", "HG", "AG"]].copy()
df2.columns = ["home", "away", "hg", "ag"]

df = pd.concat([df1, df2], ignore_index=True)
df["hg"] = pd.to_numeric(df["hg"], errors="coerce")
df["ag"] = pd.to_numeric(df["ag"], errors="coerce")
df = df.dropna(subset=["hg", "ag"])

print("=" * 75)
print("🔍 DEBUG — Match English dengan H2H >= 5 tapi SKIP")
print("=" * 75)

count = 0
for m in english:
    h2h = cari_h2h(df, m["home"], m["away"])
    
    if len(h2h) < MIN_H2H:
        continue  # skip yang H2H < 5
    
    count += 1
    
    # Cek analisa
    ou_lines = m.get("ou_lines", [])
    stats = analisa(
        h2h, m["home"], m["away"],
        odds_home=m.get("odds_home", 0),
        odds_draw=m.get("odds_draw", 0),
        odds_away=m.get("odds_away", 0),
        ou_lines=ou_lines,
    )
    
    print(f"\n{'─'*75}")
    print(f"#{count} {m['home']} vs {m['away']}")
    print(f"{'─'*75}")
    print(f"   H2H: {len(h2h)} match")
    
    # Hitung avg gol
    total_gols = (h2h["hg"] + h2h["ag"]).tolist()
    avg = sum(total_gols) / len(total_gols)
    print(f"   Avg gol H2H: {avg:.2f}")
    
    # Distribusi
    prob_25 = sum(1 for g in total_gols if g > 2.5) / len(total_gols) * 100
    prob_30 = sum(1 for g in total_gols if g > 3.0) / len(total_gols) * 100
    prob_35 = sum(1 for g in total_gols if g > 3.5) / len(total_gols) * 100
    print(f"   Prob: O2.5={prob_25:.0f}% | O3.0={prob_30:.0f}% | O3.5={prob_35:.0f}%")
    
    # Market lines
    print(f"   Market lines: {[o['line'] for o in ou_lines]}")
    
    # Analisa result
    if stats is None:
        print(f"   ❌ SKIP — analisa() return None")
        print(f"      Cek: MIN_H2H={MIN_H2H}, MIN_CONF_PICK={MIN_CONF_PICK}")
        print(f"      Kemungkinan: kandidat kosong karena avg di antara 1.8-3.0")
    else:
        print(f"   ✅ Analisa OK: {stats.get('pick')} ({stats.get('pick_conf')}%) | Skor: {stats.get('skor')}")

print(f"\n{'='*75}")
print(f"Total match dengan H2H >= 5: {count}")
print(f"{'='*75}")
