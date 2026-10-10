"""
CARI ID LIGA — Portugal, Greece, Mexico
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Coba ID di sekitar range yang mungkin
KANDIDAT = {
    "Liga Portugal": list(range(60, 90)),
    "Greece Super League": list(range(70, 90)),
    "Mexico Liga MX": list(range(65, 90)),
}

found = {}

for liga, ids in KANDIDAT.items():
    print(f"\n{'='*60}")
    print(f"🔍 {liga}")
    print(f"{'='*60}")
    
    for lid in ids:
        if lid in found.values():
            continue  # skip ID yang sudah ke-assign
        try:
            url = f"https://www.fotmob.com/api/data/leagues?id={lid}"
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code != 200:
                continue
            
            data = r.json()
            nama = data.get("details", {}).get("name", "?")
            negara = data.get("details", {}).get("country", "?")
            
            # Cek apakah cocok
            nama_low = nama.lower()
            cocok = False
            
            if "portugal" in liga.lower() and "portug" in nama_low:
                cocok = True
            elif "greece" in liga.lower() and ("greek" in nama_low or "super league" in nama_low) and negara == "GRE":
                cocok = True
            elif "mexico" in liga.lower() and ("mexic" in nama_low or "liga mx" in nama_low):
                cocok = True
            
            emoji = "✅" if cocok else ""
            if cocok:
                print(f"  {emoji} ID {lid}: {nama} ({negara})")
                if liga not in found:
                    found[liga] = lid
                    break
            # Tampilkan semua untuk inspeksi
            elif negara in ["POR", "GRE", "MEX"]:
                print(f"     ID {lid}: {nama} ({negara})")
        except:
            pass

print(f"\n{'='*60}")
print(f"🎯 HASIL:")
for liga, lid in found.items():
    print(f"  {liga} → ID {lid}")
print(f"{'='*60}")
