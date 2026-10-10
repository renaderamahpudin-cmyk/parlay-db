"""
TEST: Fotmob leagues endpoint — cari fixtures/results
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# EPL id=47, Bundesliga id=54
url = "https://www.fotmob.com/api/data/leagues?id=47"

r = requests.get(url, headers=headers, timeout=15)
data = r.json()

print("=" * 60)
print("📊 EXPLORE LEAGUES ENDPOINT")
print("=" * 60)

print(f"\nTop-level keys: {list(data.keys())}")

# Cek 'tabs'
if "tabs" in data:
    print(f"\nTabs: {len(data['tabs'])}")
    for i, tab in enumerate(data["tabs"][:10]):
        if isinstance(tab, dict):
            print(f"  [{i}] {tab.get('title', '?')} (type: {tab.get('type', '?')})")

# Cek 'table'
if "table" in data:
    print(f"\nTable: {len(data['table'])} groups")
    for t in data["table"][:2]:
        if isinstance(t, dict):
            print(f"  Keys: {list(t.keys())}")
            # Coba cari matches
            if "data" in t:
                print(f"  data keys: {list(t['data'].keys())}")

# Cek 'fixtures' atau 'matches'
for key in ["fixtures", "matches", "results"]:
    if key in data:
        print(f"\n✅ {key}: {len(data[key])} items")
        print(json.dumps(data[key][:2], indent=2, default=str)[:500])
