"""
Cari Fotmob ID untuk 13 liga
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Perkiraan ID Fotmob (perlu test)
KANDIDAT = {
    "AUSTRIA BUNDESLIGA": [41],
    "ENGLISH CHAMPIONSHIP": [48],
    "ENGLISH PREMIER LEAGUE": [47],
    "FRANCE LIGUE 1": [53],
    "GERMANY BUNDESLIGA 2": [122, 146],
    "GREECE SUPER LEAGUE": [76, 152],
    "ITALY SERIE A": [55],
    "LIGA PORTUGAL": [61],
    "MEXICO PRIMERA DIVISION": [68],
    "NETHERLANDS EREDIVISIE": [57],
    "SWEDEN ALLSVENSKAN": [67, 131],
    "TURKIYE SUPER LEAGUE": [71],
    "USA MAJOR LEAGUE SOCCER": [130],
}

mapping = {}

for liga, ids in KANDIDAT.items():
    print(f"\n{liga}")
    for lid in ids:
        url = f"https://www.fotmob.com/api/data/leagues?id={lid}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                print(f"  ID {lid}: ❌ status {r.status_code}")
                continue
            
            data = r.json()
            nama = data.get("details", {}).get("name", "?")
            negara = data.get("details", {}).get("country", "?")
            
            # Cek match dengan nama kita
            match = liga.lower() in nama.lower() or any(
                w in nama.lower() for w in liga.lower().split() if len(w) > 3
            )
            
            emoji = "✅" if match else "⚠️"
            print(f"  {emoji} ID {lid}: {nama} ({negara})")
            
            if match and liga not in mapping:
                mapping[liga] = {"id": lid, "nama_fotmob": nama, "negara": negara}
        except Exception as e:
            print(f"  ID {lid}: ❌ error")
    
    if liga not in mapping:
        print(f"  ⚠️ {liga}: BELUM KETEMU — perlu cari manual")

# Simpan
with open("output/mapping_liga.json", "w") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Mapping tersimpan: {len(mapping)}/{len(KANDIDAT)} liga")
print(f"💾 File: output/mapping_liga.json")
print("=" * 60)

# Tampilkan singkat
print("\nRINGKASAN:")
for liga, info in mapping.items():
    print(f"  {liga} → ID {info['id']}")
