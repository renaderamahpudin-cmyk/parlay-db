"""
TEST 14: Cari endpoint search Fotmob yang benar
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

term = "Borussia+Dortmund"

# Coba berbagai endpoint search
endpoints = [
    f"https://www.fotmob.com/api/searchapi/?term={term}",
    f"https://www.fotmob.com/api/search/?term={term}",
    f"https://www.fotmob.com/api/search/suggest?term={term}",
    f"https://www.fotmob.com/api/search/suggestions?term={term}",
    f"https://www.fotmob.com/api/data/search?term={term}",
    f"https://www.fotmob.com/api/data/searchapi/?term={term}",
    f"https://www.fotmob.com/searchapi/?term={term}",
    f"https://www.fotmob.com/api/teams/search?term={term}",
    # Alternatif - pakai path team langsung
    f"https://www.fotmob.com/teams/borussia-dortmund/overview",
    # Cek liga — mungkin bisa cari tim dari liga
    f"https://www.fotmob.com/api/data/leagues?id=54",
]

print("=" * 70)
print("TEST 14: CARI ENDPOINT SEARCH FOTMOB")
print("=" * 70)

for url in endpoints:
    print(f"\n🔍 {url}")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        print(f"   Panjang: {len(r.text):,}")
        print(f"   Content-Type: {r.headers.get('Content-Type', '-')[:50]}")
        
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type", "")
            if "json" in content_type:
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"   ✅ JSON! Keys: {list(data.keys())[:8]}")
                    elif isinstance(data, list):
                        print(f"   ✅ JSON list: {len(data)} items")
                        if data:
                            print(f"   Sample: {json.dumps(data[0])[:200]}")
                except:
                    print(f"   ⚠️ Bukan JSON valid")
            else:
                print(f"   ✅ HTML (bukan JSON)")
        else:
            print(f"   ❌ Gagal")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
