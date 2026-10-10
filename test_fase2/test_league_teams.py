"""
TEST 17: Ambil ID tim dari endpoint liga
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Liga ID di Fotmob:
# 47 = Premier League
# 54 = La Liga
# 55 = Serie A
# 53 = Bundesliga
# 87 = Ligue 1

LIGA = {
    "Premier League": 47,
    "La Liga": 54,
    "Serie A": 55,
    "Bundesliga": 53,
    "Ligue 1": 87,
}

print("=" * 70)
print("TEST 17: AMBIL ID TIM DARI LIGA")
print("=" * 70)

for nama_liga, liga_id in LIGA.items():
    print(f"\n🔍 {nama_liga} (id={liga_id})")
    
    url = f"https://www.fotmob.com/api/data/leagues?id={liga_id}"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"   ❌ Status {r.status_code}")
            continue
        
        data = r.json()
        
        # Cek 'table'
        table = data.get("table", [])
        print(f"   Table groups: {len(table)}")
        
        # Biasanya table[0].data.table.all = list tim
        for tbl in table[:1]:
            if isinstance(tbl, dict):
                tbl_data = tbl.get("data", {})
                table_data = tbl_data.get("table", {})
                all_teams = table_data.get("all", [])
                
                print(f"   Tim: {len(all_teams)}")
                
                for team in all_teams[:5]:
                    if isinstance(team, dict):
                        tid = team.get("id")
                        tname = team.get("name", "?")
                        print(f"      ✅ {tname}: {tid}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
