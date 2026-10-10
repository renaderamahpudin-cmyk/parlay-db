import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Coba beberapa ID untuk 4 liga
KANDIDAT = {
    "Austria Bundesliga": [38, 39, 40, 42, 43, 44],
    "Greece Super League": [75, 77, 78, 79, 80, 151, 153],
    "Liga Portugal": [62, 63, 64, 65, 66, 70],
    "Mexico Liga MX": [69, 70, 72, 73, 74, 75],
}

for liga, ids in KANDIDAT.items():
    print(f"\n{liga}")
    for lid in ids:
        try:
            url = f"https://www.fotmob.com/api/data/leagues?id={lid}"
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code != 200:
                continue
            data = r.json()
            nama = data.get("details", {}).get("name", "?")
            negara = data.get("details", {}).get("country", "?")
            print(f"  ID {lid}: {nama} ({negara})")
        except:
            pass
