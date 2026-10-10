"""
TEST 1: Cek akses ke Transfermarkt
"""
import requests

print("=" * 60)
print("TEST 1: AKSES TRANSFERMARKT")
print("=" * 60)

# URL test — halaman Barcelona
url = "https://www.transfermarkt.com/fc-barcelona/startseite/verein/131"

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

try:
    r = requests.get(url, headers=headers, timeout=15)
    print(f"\n✅ Status: {r.status_code}")
    print(f"   Panjang HTML: {len(r.text):,} karakter")
    print(f"   Content-Type: {r.headers.get('Content-Type', '-')}")
    
    # Simpan
    with open("test_akses.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"   💾 Disimpan: test_akses.html")
    
    # Cek title
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "lxml")
    if soup.title:
        print(f"   📄 Title: {soup.title.string}")
    
    # Cek apakah di-block
    if "cloudflare" in r.text.lower() or "captcha" in r.text.lower():
        print(f"   ⚠️  Terdeteksi Cloudflare/Captcha!")
    else:
        print(f"   ✅ Tidak ada Cloudflare")
    
    # Cek kata kunci
    keywords = ["injury", "Verletzung", "cedera", "player", "Spieler"]
    found = [k for k in keywords if k.lower() in r.text.lower()]
    print(f"   🔍 Keyword ditemukan: {found}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"   Kemungkinan: network, timeout, atau IP di-block")

print("\n" + "=" * 60)
