"""
TEST 4: Alternatif — ESPN, BBC, Fotmob endpoint baru
"""
import requests

print("=" * 60)
print("TEST 4: ALTERNATIF SUMBER")
print("=" * 60)

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Accept": "text/html,application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# Test berbagai URL
tests = [
    # ESPN - biasanya ramah
    ("ESPN Premier League", "https://www.espn.com/soccer/standings/_/league/eng.1"),
    ("ESPN Barcelona", "https://www.espn.com/soccer/team/_/id/83/barcelona"),
    
    # BBC Sport
    ("BBC Sport", "https://www.bbc.com/sport/football/premier-league"),
    
    # Fotmob - endpoint baru
    ("Fotmob New API", "https://www.fotmob.com/api/data/teams?id=8456"),
    ("Fotmob Match", "https://www.fotmob.com/api/matchDetails?matchId=4193846"),
    
    # Understat
    ("Understat", "https://understat.com/league/EPL"),
    
    # FBref (StatsBomb)
    ("FBref", "https://fbref.com/en/comps/9/Premier-League-Stats"),
]

for nama, url in tests:
    print(f"\n🔍 {nama}")
    print(f"   URL: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"   Status: {r.status_code}")
        print(f"   Panjang: {len(r.text):,} karakter")
        print(f"   Content-Type: {r.headers.get('Content-Type', '-')[:50]}")
        
        if r.status_code == 200:
            # Cek JSON
            if "json" in r.headers.get("Content-Type", "").lower():
                try:
                    data = r.json()
                    print(f"   ✅ JSON valid! Keys: {list(data.keys())[:5]}")
                except:
                    print(f"   ⚠️ Bukan JSON valid")
            else:
                # HTML
                if "cloudflare" in r.text.lower() or "captcha" in r.text.lower():
                    print(f"   ⚠️  Cloudflare/Captcha")
                else:
                    print(f"   ✅ HTML bersih")
        else:
            print(f"   ❌ Gagal")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
