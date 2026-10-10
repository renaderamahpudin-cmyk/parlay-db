"""
CEK MATCH LIGA INGGRIS — Kenapa Ada yang Skip?
"""
import json
import sys
sys.path.insert(0, "scripts")
from parlay_builder_v3 import cari_h2h, analisa, MIN_H2H
import pandas as pd

# Load match
with open("output/match_full.json") as f:
    matches = json.load(f)

# Load best_pick (yang lolos)
with open("output/best_pick.json") as f:
    picks = json.load(f)
pick_keys = set((p["home"].lower(), p["away"].lower()) for p in picks)

# Filter English
english_leagues = ["ENGLISH PREMIER LEAGUE", "ENGLISH CHAMPIONSHIP", 
                   "ENGLISH LEAGUE ONE", "ENGLISH LEAGUE TWO",
                   "ENGLAND PREMIER LEAGUE", "ENGLAND CHAMPIONSHIP"]

english_matches = [m for m in matches if any(
    e in m["liga"].upper() for e in ["ENGLISH", "ENGLAND"]
)]

print("=" * 75)
print(f"📊 CEK {len(english_matches)} MATCH LIGA INGGRIS")
print("=" * 75)

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

for m in english_matches:
    key = (m["home"].lower(), m["away"].lower())
    lolos = key in pick_keys
    status = "✅ LOLOS" if lolos else "❌ SKIP"
    
    print(f"\n{status} — [{m['liga']}]")
    print(f"   {m['home']} vs {m['away']} ({m['waktu']})")
    
    # Cek H2H
    h2h = cari_h2h(df, m["home"], m["away"])
    print(f"   H2H ditemukan: {len(h2h)} match")
    
    if len(h2h) < MIN_H2H:
        print(f"   → SKIP karena H2H < {MIN_H2H}")
        continue
    
    # Cek analisa
    ou_lines = m.get("ou_lines", [])
    stats = analisa(
        h2h, m["home"], m["away"],
        odds_home=m.get("odds_home", 0),
        odds_draw=m.get("odds_draw", 0),
        odds_away=m.get("odds_away", 0),
        ou_lines=ou_lines,
    )
    
    if stats is None:
        print(f"   → SKIP karena filter analisa (kandidat/conf/gap)")
        # Tampilkan detail kandidat
        gol_total = h2h["hg"].sum() + h2h["ag"].sum()
        avg = gol_total / len(h2h)
        print(f"      Avg gol H2H: {avg:.2f}")
        print(f"      OU lines market: {[o['line'] for o in ou_lines]}")
    else:
        print(f"   → Analisa OK: {stats.get('pick')} ({stats.get('pick_conf')}%)")
        print(f"      Skor: {stats.get('skor')} | Sinyal: {stats.get('sinyal')}")
        # Kalau lolos analisa tapi tidak masuk pick, berarti filter lain
        if not lolos:
            print(f"      ⚠️ LOLOS analisa TAPI tidak masuk pick — cek filter main()")

print("\n" + "=" * 75)
