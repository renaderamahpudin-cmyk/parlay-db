"""
TEST 10: Parse cedera dari Fotmob + Save cache
"""
import requests
import json
import os
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Buat folder cache
os.makedirs("cache_cedera", exist_ok=True)

TIM_IDS = {
    "Manchester City": 8456,
    "Manchester United": 10260,
    "Liverpool": 8650,
    "Arsenal": 9825,
    "Chelsea": 8455,
    "Barcelona": 8634,
    "Real Madrid": 8633,
    "Bayern Munich": 9823,
    "PSG": 9847,
    "Juventus": 9885,
}

print("=" * 70)
print("TEST 10: PARSE CEDERA + SAVE CACHE")
print("=" * 70)

all_data = {}

for nama, tid in TIM_IDS.items():
    print(f"\n🔍 {nama}")
    try:
        url = f"https://www.fotmob.com/api/data/teams?id={tid}"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code != 200:
            print(f"   ❌ Status {r.status_code}")
            continue
        
        data = r.json()
        squad_groups = data.get("squad", {}).get("squad", [])
        
        cedera_list = []
        for grup in squad_groups:
            role_group = grup.get("title", "?")
            for member in grup.get("members", []):
                injury = member.get("injury")
                if injury is not None and injury != "None":
                    cedera_list.append({
                        "nama": member.get("name"),
                        "posisi": member.get("role", {}).get("fallback", role_group),
                        "expectedReturn": injury.get("expectedReturn", "?"),
                    })
        
        # Klasifikasi keparahan
        for c in cedera_list:
            ret = c["expectedReturn"].lower()
            if "out for" in ret or "month" in ret:
                c["severity"] = "LAMA"
            elif "doubtful" in ret:
                c["severity"] = "DOUBTFUL"
            elif "back in training" in ret or "few weeks" in ret:
                c["severity"] = "RINGAN"
            else:
                c["severity"] = "SEDANG"
        
        # Simpan
        cache = {
            "team_name": nama,
            "team_id": tid,
            "fetched_at": datetime.now().isoformat(),
            "total_cedera": len(cedera_list),
            "cedera": cedera_list,
        }
        
        cache_file = f"cache_cedera/cedera_{tid}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        all_data[nama] = cache
        
        # Group by severity
        from collections import Counter
        sev_count = Counter(c["severity"] for c in cedera_list)
        
        print(f"   ✅ Total: {len(cedera_list)} cedera")
        print(f"      {dict(sev_count)}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Simpan gabungan
with open("cache_cedera/all_cedera.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"✅ Cache disimpan di: test_fase2/cache_cedera/")
print(f"   Total tim: {len(all_data)}")
print(f"{'='*70}")
