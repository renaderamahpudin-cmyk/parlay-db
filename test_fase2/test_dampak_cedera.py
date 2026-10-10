"""
TEST 11: Dampak cedera ke confidence match
"""
import json
import os

print("=" * 70)
print("TEST 11: DAMPAK CEDERA KE MATCH")
print("=" * 70)

# Load cache cedera
with open("cache_cedera/all_cedera.json", "r", encoding="utf-8") as f:
    all_cedera = json.load(f)

# Load match hari ini
with open("/root/parlay-db/output/best_pick.json", "r", encoding="utf-8") as f:
    picks = json.load(f)

print(f"\n📊 Pick: {len(picks)} match")
print(f"📊 Tim di cache: {len(all_cedera)}\n")

# Mapping nama tim → tim di cache
def cari_tim_di_cache(nama):
    """Cari tim di cache dengan fuzzy match"""
    nama_lower = nama.lower()
    for team_name, data in all_cedera.items():
        team_lower = team_name.lower()
        # Cek partial match
        for word in nama_lower.split():
            if len(word) >= 4 and word in team_lower:
                return team_name, data
    return None, None

# Analisa per match
print("=" * 70)
print("📊 ANALISA DAMPAK PER MATCH")
print("=" * 70)

for i, pick in enumerate(picks, 1):
    home = pick.get("home", "?")
    away = pick.get("away", "?")
    
    # Cari di cache
    home_team, home_data = cari_tim_di_cache(home)
    away_team, away_data = cari_tim_di_cache(away)
    
    print(f"\n#{i} {home} vs {away}")
    print(f"   Pick: {pick.get('pick', '?')} ({pick.get('pick_conf', 0)}%)")
    
    if home_team:
        sev = home_data.get("cedera", [])
        from collections import Counter
        c = Counter(x["severity"] for x in sev)
        print(f"   🏠 HOME: {home} = {home_team}")
        print(f"      Cedera: {len(sev)} ({dict(c)})")
    else:
        print(f"   🏠 HOME: {home} — ⚠️ tidak ada di cache")
    
    if away_team:
        sev = away_data.get("cedera", [])
        from collections import Counter
        c = Counter(x["severity"] for x in sev)
        print(f"   ✈️  AWAY: {away} = {away_team}")
        print(f"      Cedera: {len(sev)} ({dict(c)})")
    else:
        print(f"   ✈️  AWAY: {away} — ⚠️ tidak ada di cache")
    
    # Hitung dampak
    if home_data and away_data:
        home_bad = sum(1 for x in home_data.get("cedera", []) 
                       if x["severity"] in ["SEDANG", "LAMA"])
        away_bad = sum(1 for x in away_data.get("cedera", []) 
                       if x["severity"] in ["SEDANG", "LAMA"])
        
        diff = home_bad - away_bad
        if diff > 0:
            print(f"   ⚠️  Dampak: AWAY lebih diuntungkan (+{diff})")
        elif diff < 0:
            print(f"   ⚠️  Dampak: HOME lebih diuntungkan (+{-diff})")
        else:
            print(f"   ✅ Dampak: Seimbang")

print("\n" + "=" * 70)
