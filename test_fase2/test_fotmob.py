"""
TEST 2: Cek akses ke Fotmob
"""
import requests

print("=" * 60)
print("TEST 2: AKSES FOTMOB")
print("=" * 60)

# Fotmob pakai API JSON internal
# Coba endpoint basic
urls = [
    "https://www.fotmob.com/api/teams?id=8456",  # Barcelona
    "https://www.fotmob.com/api/teams?id=8633",  # Real Madrid
    "https://www.fotmob.com/api/leagues?id=47",  # Premier League
]

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

for url in urls:
    print(f"\n🔍 Test: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        print(f"   Panjang: {len(r.text):,} karakter")
        print(f"   Content-Type: {r.headers.get('Content-Type', '-')}")
        
        if r.status_code == 200:
            # Coba parse JSON
            try:
                data = r.json()
                print(f"   ✅ JSON valid!")
                print(f"   Keys: {list(data.keys())[:5]}")
            except Exception as e:
                print(f"   ⚠️ Bukan JSON: {e}")
                print(f"   Preview: {r.text[:200]}")
        else:
            print(f"   ❌ Gagal")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
