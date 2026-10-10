"""
TEST 3: Cek akses ke Sofascore
"""
import requests

print("=" * 60)
print("TEST 3: AKSES SOFASCORE")
print("=" * 60)

# Sofascore API internal
urls = [
    "https://api.sofascore.com/api/v1/team/2817",  # Barcelona
    "https://api.sofascore.com/api/v1/team/2829",  # Real Madrid
    "https://api.sofascore.com/api/v1/unique-tournament/17",  # Premier League
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
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"   ✅ JSON valid!")
                print(f"   Keys: {list(data.keys())[:5]}")
            except:
                print(f"   ⚠️ Bukan JSON")
        else:
            print(f"   ❌ Gagal")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
