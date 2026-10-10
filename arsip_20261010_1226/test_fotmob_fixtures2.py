"""
TEST: Fotmob fixtures — handle dict
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

url = "https://www.fotmob.com/api/data/leagues?id=47"
r = requests.get(url, headers=headers, timeout=15)
data = r.json()

fixtures = data.get("fixtures", {})

print("=" * 60)
print("📊 EXPLORE FIXTURES")
print("=" * 60)

print(f"\nTipe fixtures: {type(fixtures).__name__}")

if isinstance(fixtures, dict):
    print(f"Keys: {list(fixtures.keys())}")
    for k, v in fixtures.items():
        print(f"\n  [{k}] tipe: {type(v).__name__}")
        if isinstance(v, list):
            print(f"    Panjang: {len(v)}")
            if len(v) > 0:
                print(f"    Sample [0]:")
                print(json.dumps(v[0], indent=2, default=str)[:800])
        elif isinstance(v, dict):
            print(f"    Keys: {list(v.keys())[:10]}")
            # Coba explore
            for k2, v2 in list(v.items())[:3]:
                print(f"      [{k2}] {type(v2).__name__}: {str(v2)[:100]}")

# Simpan buat inspeksi
with open("output/fotmob_league47.json", "w") as f:
    json.dump(data, f, indent=2, default=str)
print(f"\n💾 Disimpan: output/fotmob_league47.json")
