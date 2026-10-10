"""
TEST 16: Parse hasil search Fotmob
"""
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "text/html,application/json",
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
print("TEST 16: PARSE SEARCH FOTMOB")
print("=" * 70)

for nama in TIM_TEST:
    print(f"\n🔍 {nama}")
    
    # Pakai endpoint searchapi
    url = f"https://www.fotmob.com/searchapi/?term={nama.replace(' ', '+')}"
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code != 200:
            print(f"   ❌ Status {r.status_code}")
            continue
        
        # Simpan HTML untuk inspeksi
        filename = f"search_{nama.replace(' ', '_')}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(r.text)
        
        # Parse HTML
        soup = BeautifulSoup(r.text, "lxml")
        
        # Cari link tim — biasanya ada di <a href="/teams/...">
        links = soup.find_all("a", href=True)
        team_links = []
        for a in links:
            href = a["href"]
            if "/teams/" in href:
                team_links.append({
                    "text": a.get_text(strip=True),
                    "href": href,
                })
        
        # Ambil ID dari href
        import re
        for tl in team_links[:5]:
            # Format: /teams/slug/overview?id=XXXXX
            match = re.search(r'id=(\d+)', tl["href"])
            if match:
                tid = match.group(1)
                print(f"   ✅ ID {tid}: {tl['text']} → {tl['href'][:60]}")
            else:
                print(f"   ⚠️ {tl['text']} → {tl['href'][:60]}")
        
        if not team_links:
            print(f"   ⚠️  Tidak ada link tim — cek {filename}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
