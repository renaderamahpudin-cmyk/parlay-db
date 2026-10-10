"""
TEST 9: Cari pemain cedera di beberapa tim
"""
import requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ID tim yang perlu ditest (kita cari nanti)
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
print("TEST 9: CARI PEMAIN CEDERA")
print("=" * 70)

total_cedera = 0

for nama, tid in TIM_IDS.items():
    print(f"\n🔍 {nama} (id={tid})")
    try:
        url = f"https://www.fotmob.com/api/data/teams?id={tid}"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code != 200:
            print(f"   ❌ Status {r.status_code}")
            continue
        
        data = r.json()
        squad_groups = data.get("squad", {}).get("squad", [])
        
        # Scan semua pemain
        pemain_cedera = []
        for grup in squad_groups:
            for member in grup.get("members", []):
                injury = member.get("injury")
                if injury is not None and injury != "None":
                    pemain_cedera.append({
                        "nama": member.get("name"),
                        "role": member.get("role", {}).get("fallback", "?"),
                        "injury": injury,
                    })
        
        print(f"   Squad: {sum(len(g.get('members', [])) for g in squad_groups)} pemain")
        print(f"   🔴 Cedera: {len(pemain_cedera)}")
        
        if pemain_cedera:
            total_cedera += len(pemain_cedera)
            print(f"   Detail:")
            for p in pemain_cedera[:3]:
                print(f"      - {p['nama']} ({p['role']})")
                print(f"        injury: {json.dumps(p['injury'])[:100]}")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n{'='*70}")
print(f"TOTAL PEMAIN CEDERA: {total_cedera}")
print(f"{'='*70}")
