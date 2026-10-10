"""
Update Portugal + Test ID Greece & Mexico
"""
import json
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# 1. Update Portugal dulu
with open("output/mapping_liga.json") as f:
    mapping = json.load(f)

mapping["LIGA PORTUGAL"] = {"id": 61, "negara": "POR"}
with open("output/mapping_liga.json", "w") as f:
    json.dump(mapping, f, indent=2, ensure_ascii=False)
print("✅ Portugal ID 61 ditambah ke mapping\n")

# 2. Test ID Greece & Mexico
KANDIDAT = {
    "Greece Super League": [76, 77, 78, 79, 80, 151, 152, 153, 154, 155],
    "Mexico Liga MX": [68, 69, 70, 72, 73, 74, 75, 131, 132, 133],
}

found = {}
for liga, ids in KANDIDAT.items():
    print(f"🔍 {liga}")
    for lid in ids:
        try:
            url = f"https://www.fotmob.com/api/data/leagues?id={lid}"
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code != 200:
                continue
            data = r.json()
            nama = data.get("details", {}).get("name", "?")
            negara = data.get("details", {}).get("country", "?")
            
            # Cocokkan
            cocok = False
            if "greece" in liga.lower() and negara == "GRE" and "super league" in nama.lower():
                cocok = True
            elif "mexico" in liga.lower() and negara == "MEX" and "liga mx" in nama.lower():
                cocok = True
            
            if cocok:
                print(f"  ✅ ID {lid}: {nama} ({negara})")
                found[liga] = lid
                break
            elif negara in ["GRE", "MEX"]:
                print(f"     ID {lid}: {nama} ({negara})")
        except:
            pass

print(f"\n🎯 HASIL:")
for liga, lid in found.items():
    print(f"  {liga} → ID {lid}")
