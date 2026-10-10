"""
TEST 5: Eksplorasi struktur Fotmob JSON
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Barcelona team ID
url = "https://www.fotmob.com/api/data/teams?id=8456"

print("=" * 60)
print("TEST 5: EKSPLORASI FOTMOB")
print("=" * 60)

r = requests.get(url, headers=headers, timeout=15)
data = r.json()

print(f"\n✅ Data loaded: {len(r.text):,} karakter")

# Simpan untuk inspect
with open("fotmob_barcelona.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"💾 Disimpan: fotmob_barcelona.json")

# Explore top-level keys
print(f"\n📂 TOP-LEVEL KEYS:")
for key in data.keys():
    val = data[key]
    if isinstance(val, dict):
        print(f"  {key}: dict ({len(val)} keys)")
    elif isinstance(val, list):
        print(f"  {key}: list ({len(val)} items)")
    else:
        print(f"  {key}: {type(val).__name__} = {str(val)[:50]}")

# Cek 'details'
if "details" in data:
    print(f"\n📂 'details' keys:")
    for key in data["details"].keys():
        val = data["details"][key]
        if isinstance(val, dict):
            print(f"  {key}: dict")
        elif isinstance(val, list):
            print(f"  {key}: list ({len(val)})")
        else:
            print(f"  {key}: {str(val)[:50]}")

# Cek 'tabs'
if "tabs" in data:
    print(f"\n📂 'tabs' (list {len(data['tabs'])} items):")
    for i, tab in enumerate(data["tabs"][:5]):
        if isinstance(tab, dict):
            print(f"  [{i}] keys: {list(tab.keys())[:5]}")

print("\n" + "=" * 60)
