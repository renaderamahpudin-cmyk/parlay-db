"""
BUILD: Mapping tim → ID Fotmob dari 5 liga top
"""
import requests
import json
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ID liga Fotmob yang benar
LIGA = {
    "Premier League": 47,
    "La Liga": 87,
    "Serie A": 55,
    "Bundesliga": 54,
    "Ligue 1": 53,
    "Eredivisie": 57,
    "Primeira Liga": 61,
    "Championship": 48,
}

print("=" * 70)
print("BUILD TEAM MAPPING")
print("=" * 70)

mapping = {}

for nama_liga, liga_id in LIGA.items():
    print(f"\n🔍 {nama_liga} (id={liga_id})")
    
    url = f"https://www.fotmob.com/api/data/leagues?id={liga_id}"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"   ❌ Status {r.status_code}")
            continue
        
        data = r.json()
        table = data.get("table", [])
        
        if not table:
            print(f"   ⚠️ Tidak ada table")
            continue
        
        # Ambil tim dari table
        all_teams = table[0].get("data", {}).get("table", {}).get("all", [])
        
        print(f"   Tim: {len(all_teams)}")
        
        for team in all_teams:
            tid = team.get("id")
            tname = team.get("name", "?")
            if tid and tname:
                mapping[tname] = {
                    "id": tid,
                    "liga": nama_liga,
                }
                # Tampilkan 2 saja
                if len([k for k, v in mapping.items() if v["liga"] == nama_liga]) <= 2:
                    print(f"      ✅ {tname}: {tid}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Simpan
with open("team_ids.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"✅ Total tim: {len(mapping)}")
print(f"💾 Disimpan: team_ids.json")
print(f"{'='*70}")

# Tampilkan summary per liga
from collections import Counter
liga_count = Counter(v["liga"] for v in mapping.values())
print(f"\n📊 Per liga:")
for liga, count in sorted(liga_count.items(), key=lambda x: -x[1]):
    print(f"   {liga:20} {count} tim")
