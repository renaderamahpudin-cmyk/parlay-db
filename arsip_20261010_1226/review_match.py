"""
REVIEW 18 MATCH — Detail Lengkap
"""
import json

with open("output/best_pick.json") as f:
    picks = json.load(f)

print("=" * 75)
print(f"📊 REVIEW {len(picks)} MATCH")
print("=" * 75)

# Sort by tier & skor
picks_sorted = sorted(picks, key=lambda x: (-x.get("skor", 0)))

for i, p in enumerate(picks_sorted, 1):
    tier = p.get("tier", "?")
    h2h = p.get("h2h", 0)
    skor = p.get("skor", 0)
    
    print(f"\n{'─'*75}")
    print(f"#{i} [{p['liga']}] {tier}")
    print(f"{'─'*75}")
    print(f"   {p['home']} vs {p['away']}  ({p['waktu']})")
    print(f"   H2H: {h2h}x | Skor: {skor}")
    print(f"   Gol total H2H: {p.get('gol_total', '?')}")
    
    # Pick
    pick = p.get("pick", "?")
    conf = p.get("pick_conf", 0)
    odds = p.get("pick_odds", 0)
    print(f"\n   ⚽ PICK: {pick}")
    print(f"      Confidence: {conf}%")
    print(f"      Odds: {odds}")
    
    # Value gap
    gap = p.get("value_gap", 0)
    kat = p.get("kategori_gap", "?")
    print(f"      Value Gap: {gap:+.1f}% ({kat})")
    
    # Top 1x2 & top ou
    top_ou = p.get("top_ou")
    if top_ou:
        print(f"\n   📊 Market O/U:")
        print(f"      {top_ou['pick']} @ {top_ou['odds']} | prob {top_ou['prob']}% | gap {top_ou['gap']:+.1f}%")
    
    # Titik buta
    titik = p.get("titik_buta")
    if titik:
        over_rate = titik.get("over_rate", 0)
        ada = "ADA" if titik.get("ada_di_market") else "TIDAK ADA"
        print(f"\n   📌 TITIK BUTA 2.5: O={over_rate:.0f}% ({ada} di market)")

print(f"\n{'='*75}")
print(f"✅ Total: {len(picks)} match")
print(f"   T1: {sum(1 for p in picks if 'T1' in p.get('tier', ''))}")
print(f"   T2: {sum(1 for p in picks if 'T2' in p.get('tier', ''))}")
print(f"   T3: {sum(1 for p in picks if 'T3' in p.get('tier', ''))}")
print(f"{'='*75}")
