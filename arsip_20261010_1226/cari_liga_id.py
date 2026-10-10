"""
Cari Fotmob ID untuk liga yang belum
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Liga yang perlu dicari ID
LIGA_NAMA = [
    "Super Lig",           # Turki
    "Allsvenskan",         # Swedia
    "MLS",                 # USA
    "Liga MX",             # Mexico
    "Super League",        # Yunani
    "Bundesliga",          # Austria
    "Bundesliga 2",        # Jerman 2
    "Championship",        # Inggris 2
]

# Fotmob search untuk tiap liga
print("=" * 60)
print("🔍 CARI FOTMOB ID LIGA")
print("=" * 60)

for nama in LIGA_NAMA:
    print(f"\n🔍 {nama}")
    # Coba endpoint search
    url = f"https://www.fotmob.com/api/searchapi/?term={nama.replace(' ', '+')}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        # Kita tahu ini HTML, tapi coba lihat apakah ada JSON di response
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Alternatif: pakai leagues tanpa ID untuk lihat popular
print("\n" + "=" * 60)
print("📊 POPULAR LEAGUES DARI FOTMOB")
print("=" * 60)

# Coba endpoint all leagues
urls = [
    "https://www.fotmob.com/api/allLeagues",
    "https://www.fotmob.com/api/leagues",
    "https://www.fotmob.com/api/data/allLeagues",
]
for u in urls:
    print(f"\n🔍 {u}")
    try:
        r = requests.get(u, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            try:
                data = r.json()
                if isinstance(data, dict):
                    print(f"   Keys: {list(data.keys())[:10]}")
            except:
                pass
    except:
        pass
