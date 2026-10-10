"""
TEST 13: Auto-fetch ID Fotmob dari search API
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Test dengan beberapa tim
TIM_TEST = [
    "Borussia Dortmund",
    "PSV Eindhoven",
    "Galatasaray",
    "Cork City",
    "Jong Ajax",
    "Werder Bremen",
]

print("=" * 70)
print("TEST 13: AUTO-FETCH ID FOTMOB")
print("=" * 70)

for nama in TIM_TEST:
    print(f"\n🔍 {nama}")
    
    # Coba search endpoint
    url = f"https://www.fotmob.com/api/searchapi/?term={nama.replace(' ', '+')}"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"   Keys: {list(data.keys())[:5]}")
                
                # Cari tim di hasil
                if isinstance(data, dict):
                    # Cek berbagai struktur
                    if "teams" in data:
                        teams = data["teams"]
                        print(f"   Teams: {len(teams)}")
                        for t in teams[:3]:
                            print(f"      - {t}")
                    elif "suggestion" in data:
                        sug = data["suggestion"]
                        print(f"   Suggestions: {len(sug)}")
                        for s in sug[:3]:
                            print(f"      - {s}")
                    else:
                        # Tampilkan preview
                        print(f"   Preview: {json.dumps(data)[:300]}")
                elif isinstance(data, list):
                    print(f"   List: {len(data)} items")
                    for item in data[:3]:
                        print(f"      - {item}")
            except Exception as e:
                print(f"   ⚠️ JSON error: {e}")
                print(f"   Preview: {r.text[:200]}")
        else:
            print(f"   ❌ Gagal")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
