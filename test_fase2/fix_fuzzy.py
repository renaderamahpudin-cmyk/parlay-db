"""
TEST 12: Fix fuzzy matching (anti false positive)
"""
import json

print("=" * 70)
print("TEST 12: FIX FUZZY MATCHING")
print("=" * 70)

# Load cache
with open("cache_cedera/all_cedera.json", "r", encoding="utf-8") as f:
    all_cedera = json.load(f)

# Load pick
with open("/root/parlay-db/output/best_pick.json", "r", encoding="utf-8") as f:
    picks = json.load(f)

# ===== FIX: Fuzzy matching lebih ketat =====
def cari_tim_di_cache(nama):
    """
    Cari tim di cache dengan aturan KETAT:
    1. Exact match dulu
    2. Kalau nggak, cek word match (min 2 kata)
    3. Kalau nggak, cek kemiripan > 70%
    """
    nama_lower = nama.lower().strip()
    
    # 1. Exact match
    for team_name in all_cedera.keys():
        if team_name.lower() == nama_lower:
            return team_name, all_cedera[team_name]
    
    # 2. Word match — minimal 2 kata yang sama, panjang >= 4
    nama_words = set(w for w in nama_lower.split() if len(w) >= 4)
    
    best_match = None
    best_score = 0
    
    for team_name in all_cedera.keys():
        team_words = set(w for w in team_name.lower().split() if len(w) >= 4)
        
        # Hitung irisan
        common = nama_words & team_words
        
        if len(common) >= 2:
            # Minimal 2 kata yang sama
            score = len(common)
            if score > best_score:
                best_score = score
                best_match = team_name
    
    if best_match:
        return best_match, all_cedera[best_match]
    
    return None, None


print("\n" + "=" * 70)
print("📊 ANALISA DENGAN FUZZY KETAT")
print("=" * 70)

found = 0
for i, pick in enumerate(picks, 1):
    home = pick.get("home", "?")
    away = pick.get("away", "?")
    
    home_team, home_data = cari_tim_di_cache(home)
    away_team, away_data = cari_tim_di_cache(away)
    
    print(f"\n#{i} {home} vs {away}")
    
    if home_team:
        found += 1
        print(f"   🏠 {home} = {home_team} ✅")
        if home_data:
            print(f"      Cedera: {home_data.get('total_cedera', 0)}")
    else:
        print(f"   🏠 {home} — tidak ada")
    
    if away_team:
        found += 1
        print(f"   ✈️  {away} = {away_team} ✅")
        if away_data:
            print(f"      Cedera: {away_data.get('total_cedera', 0)}")
    else:
        print(f"   ✈️  {away} — tidak ada")

print(f"\n{'='*70}")
print(f"✅ Total ketemu: {found} (dari {len(picks)*2} tim)")
print(f"{'='*70}")
