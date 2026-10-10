"""
TEST LOGIC BARU — Pick dari Market
"""
import json

print("=" * 70)
print("📊 TEST LOGIC BARU — PICK DARI MARKET")
print("=" * 70)

with open("output/best_pick.json") as f:
    picks = json.load(f)

with open("output/match_full.json") as f:
    matches = json.load(f)

# Map matches
match_map = {}
for m in matches:
    key = (m["home"].lower(), m["away"].lower())
    match_map[key] = m

for p in picks:
    key = (p["home"].lower(), p["away"].lower())
    m = match_map.get(key, {})
    ou_lines = m.get("ou_lines", [])
    
    # Cek 2.5 di market
    has_25 = any(abs(ou.get("line", 0) - 2.5) < 0.01 for ou in ou_lines)
    
    top_1x2 = p.get("top_1x2")
    top_ou = p.get("top_ou")
    titik = p.get("titik_buta")
    
    print(f"\n{'='*70}")
    print(f"{p['home']} vs {p['away']}")
    print(f"{'='*70}")
    
    market_lines = [ou['line'] for ou in ou_lines]
    print(f"  Market lines: {market_lines}")
    print(f"  2.5 ada? {'✅ YA' if has_25 else '❌ TIDAK'}")
    
    if has_25:
        # Pakai 2.5 langsung
        for ou in ou_lines:
            if abs(ou['line'] - 2.5) < 0.01:
                print(f"  → PICK: 2.5 (langsung dari market)")
                print(f"     Over: {ou['over']} | Under: {ou['under']}")
                break
    else:
        # 2.5 jadi titik buta
        if titik:
            print(f"  📌 TITIK BUTA: 2.5 = {titik['over_rate']:.0f}% (referensi)")
        
        # Kandidat market
        kandidat = []
        
        if top_1x2 and top_1x2.get("gap", 0) >= 5:
            kandidat.append({
                "jenis": "1X2",
                "pick": top_1x2["pick"],
                "odds": top_1x2["odds"],
                "prob": top_1x2["prob"],
                "gap": top_1x2["gap"],
            })
        
        if top_ou and top_ou.get("gap", 0) >= 5:
            kandidat.append({
                "jenis": "OU",
                "pick": top_ou["pick"],
                "odds": top_ou["odds"],
                "prob": top_ou["prob"],
                "gap": top_ou["gap"],
            })
        
        if kandidat:
            kandidat.sort(key=lambda x: -x["gap"])
            best = kandidat[0]
            print(f"  🎯 PICK DARI MARKET: {best['pick']} @ {best['odds']}")
            print(f"     Prob: {best['prob']}% | Gap: {best['gap']:+.1f}%")
        else:
            print(f"  ⚠️ SKIP — tidak ada kandidat bagus (gap < 5%)")

print("\n" + "=" * 70)
