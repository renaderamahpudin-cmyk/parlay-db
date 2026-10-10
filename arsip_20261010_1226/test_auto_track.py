"""
TEST: Auto-track 1 liga (EPL)
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# EPL id=47
url = "https://www.fotmob.com/api/data/leagues?id=47"
r = requests.get(url, headers=headers, timeout=15)
data = r.json()

fixtures = data.get("fixtures", {}).get("allMatches", [])
print(f"Total match EPL: {len(fixtures)}")

# Cari match yang finish + tanggal hari ini
from datetime import datetime

# Pick kita: Arsenal vs Leeds
target_home = "arsenal"
target_away = "leeds"

print(f"\nCari match: {target_home} vs {target_away}")
print("=" * 60)

for m in fixtures:
    home = m["home"]["name"].lower()
    away = m["away"]["name"].lower()
    status = m.get("status", {})
    
    # Fuzzy match
    if (target_home in home or home in target_home) and \
       (target_away in away or away in target_away):
        print(f"\n✅ Match ditemukan!")
        print(f"   ID: {m['id']}")
        print(f"   {m['home']['name']} vs {m['away']['name']}")
        print(f"   UTC time: {status.get('utcTime', '?')}")
        print(f"   Finished: {status.get('finished', '?')}")
        print(f"   Started: {status.get('started', '?')}")
        print(f"   Score: {status.get('scoreStr', '?')}")
        print(f"   Reason: {status.get('reason', {}).get('longKey', '?')}")
        break
else:
    print(f"❌ Match tidak ditemukan")
    # Tampilkan match arsenal
    print(f"\nSemua match Arsenal (sample):")
    for m in fixtures:
        if "arsenal" in m["home"]["name"].lower() or "arsenal" in m["away"]["name"].lower():
            s = m["status"]
            print(f"   {m['home']['name']} vs {m['away']['name']}")
            print(f"      Score: {s.get('scoreStr', '?')} | Finished: {s.get('finished', '?')}")
            print(f"      Time: {s.get('utcTime', '?')}")
