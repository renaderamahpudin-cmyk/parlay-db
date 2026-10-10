"""
TEST: Fotmob match endpoint untuk hasil
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Test beberapa endpoint
endpoints = [
    # Match details
    "https://www.fotmob.com/api/matchDetails?matchId=4193846",
    "https://www.fotmob.com/api/data/matchDetails?matchId=4193846",
    "https://www.fotmob.com/api/match?id=4193846",
    
    # Team fixtures
    "https://www.fotmob.com/api/data/teamFixtures?id=8456",
    "https://www.fotmob.com/api/data/team?id=8456",
    
    # League fixtures
    "https://www.fotmob.com/api/data/leagues?id=47&tab=fixtures",
    "https://www.fotmob.com/api/data/leagues?id=47&tab=results",
]

for url in endpoints:
    print(f"\n🔍 {url}")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        print(f"   Panjang: {len(r.text):,}")
        
        if r.status_code == 200:
            ct = r.headers.get("Content-Type", "")
            if "json" in ct:
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"   ✅ JSON! Keys: {list(data.keys())[:8]}")
                    elif isinstance(data, list):
                        print(f"   ✅ JSON list: {len(data)} items")
                except:
                    print(f"   ⚠️ Bukan JSON valid")
            else:
                print(f"   ✅ HTML (bukan JSON)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
