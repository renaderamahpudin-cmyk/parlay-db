"""
TEST 18: End-to-End — Match + Cedera
"""
import requests
import json
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Load mapping tim
with open("team_ids.json", "r", encoding="utf-8") as f:
    team_ids = json.load(f)

# Load match hari ini
with open("/root/parlay-db/output/best_pick.json", "r", encoding="utf-8") as f:
    picks = json.load(f)

print("=" * 70)
print("TEST 18: END-TO-END")
print("=" * 70)
print(f"📊 Match: {len(picks)}")
print(f"📊 Tim di mapping: {len(team_ids)}")

def cari_id_tim(nama):
    """Cari ID tim dengan exact + fuzzy ketat"""
    nama_lower = nama.lower().strip()
    
    # 1. Exact match
    for team_name, info in team_ids.items():
        if team_name.lower() == nama_lower:
            return info["id"], team_name
    
    # 2. Cek apakah nama match sebagian besar
    best = None
    best_score = 0
    
    for team_name, info in team_ids.items():
        team_lower = team_name.lower()
        # Cek apakah nama (atau bagiannya) ada
        if nama_lower in team_lower or team_lower in nama_lower:
            score = len(nama_lower) / max(len(team_lower), 1)
            if score > best_score:
                best_score = score
                best = (info["id"], team_name)
    
    if best and best_score > 0.5:
        return best
    return None, None

def ambil_cedera(team_id):
    """Ambil cedera dari Fotmob"""
    cache_file = f"cache_cedera/cedera_{team_id}.json"
    
    # Cek cache dulu (kalau ada, < 24 jam)
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)
        return cache
    
    # Fetch dari API
    url = f"https://www.fotmob.com/api/data/teams?id={team_id}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        
        data = r.json()
        squad_groups = data.get("squad", {}).get("squad", [])
        
        cedera_list = []
        for grup in squad_groups:
            role_group = grup.get("title", "?")
            for member in grup.get("members", []):
                injury = member.get("injury")
                if injury is not None and injury != "None":
                    ret = injury.get("expectedReturn", "?")
                    if "out for" in ret.lower() or "month" in ret.lower():
                        sev = "LAMA"
                    elif "doubtful" in ret.lower():
                        sev = "DOUBTFUL"
                    elif "back in" in ret.lower() or "few weeks" in ret.lower():
                        sev = "RINGAN"
                    else:
                        sev = "SEDANG"
                    
                    cedera_list.append({
                        "nama": member.get("name"),
                        "posisi": member.get("role", {}).get("fallback", role_group),
                        "expectedReturn": ret,
                        "severity": sev,
                    })
        
        cache = {
            "team_id": team_id,
            "total_cedera": len(cedera_list),
            "cedera": cedera_list,
        }
        
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        return cache
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# Analisa per match
print("\n" + "=" * 70)
print("📊 ANALISA MATCH")
print("=" * 70)

found = 0
for i, pick in enumerate(picks, 1):
    home = pick.get("home", "?")
    away = pick.get("away", "?")
    
    print(f"\n#{i} {home} vs {away}")
    print(f"   Pick: {pick.get('pick', '?')} ({pick.get('pick_conf', 0)}%)")
    
    home_id, home_name = cari_id_tim(home)
    away_id, away_name = cari_id_tim(away)
    
    if home_id:
        found += 1
        print(f"   🏠 {home} = {home_name} (id={home_id})")
        cedera = ambil_cedera(home_id)
        if cedera:
            from collections import Counter
            c = Counter(x["severity"] for x in cedera["cedera"])
            print(f"      Cedera: {cedera['total_cedera']} ({dict(c)})")
    else:
        print(f"   🏠 {home} — ⚠️ tidak di mapping")
    
    if away_id:
        found += 1
        print(f"   ✈️  {away} = {away_name} (id={away_id})")
        cedera = ambil_cedera(away_id)
        if cedera:
            from collections import Counter
            c = Counter(x["severity"] for x in cedera["cedera"])
            print(f"      Cedera: {cedera['total_cedera']} ({dict(c)})")
    else:
        print(f"   ✈️  {away} — ⚠️ tidak di mapping")

print(f"\n{'='*70}")
print(f"✅ Coverage: {found}/{len(picks)*2} tim ketemu")
print(f"{'='*70}")
