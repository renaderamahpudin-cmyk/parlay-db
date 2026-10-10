"""
AUDIT TEAM — Cek database tim vs mapping
"""
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import json
import os
import sys

# Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)


def load_database():
    """Load semua tim unik di database"""
    teams = set()
    
    # Top leagues
    try:
        df = pd.read_csv("data/football_data/all_football_data.csv", low_memory=False)
        df = df.dropna(subset=["HomeTeam", "AwayTeam"])
        for col in ["HomeTeam", "AwayTeam"]:
            for t in df[col].unique():
                if isinstance(t, str) and len(t.strip()) > 0:
                    teams.add(t.strip())
    except Exception as e:
        print(f"⚠️ Top: {e}")
    
    # Extra leagues
    try:
        df = pd.read_csv("data/football_data_extra/all_extra.csv", low_memory=False)
        df = df.dropna(subset=["Home", "Away"])
        for col in ["Home", "Away"]:
            for t in df[col].unique():
                if isinstance(t, str) and len(t.strip()) > 0:
                    teams.add(t.strip())
    except Exception as e:
        print(f"⚠️ Extra: {e}")
    
    return teams


def load_mapping():
    """Load team_ids.json"""
    path = "scripts/team_ids.json"
    if not os.path.exists(path):
        path = "team_ids.json"
    
    if not os.path.exists(path):
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_match():
    """Load match hari ini"""
    path = "output/match_full.json"
    if not os.path.exists(path):
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 70)
    print("🔍 AUDIT TEAM")
    print("=" * 70)
    
    # 1. Database
    print("\n[1] Database H2H...")
    db_teams = load_database()
    print(f"    ✅ Tim unik: {len(db_teams)}")
    
    # 2. Mapping
    print("\n[2] Mapping team_ids.json...")
    mapping = load_mapping()
    print(f"    ✅ Tim di mapping: {len(mapping)}")
    
    # 3. Match hari ini
    print("\n[3] Match hari ini...")
    matches = load_match()
    match_teams = set()
    for m in matches:
        if m.get("home"): match_teams.add(m["home"].strip())
        if m.get("away"): match_teams.add(m["away"].strip())
    print(f"    ✅ Tim di match: {len(match_teams)}")
    
    # 4. Coverage
    print("\n" + "=" * 70)
    print("📊 ANALISA COVERAGE")
    print("=" * 70)
    
    def normalize(n):
        return n.lower().strip() if isinstance(n, str) else ""
    
    mapping_lower = {normalize(k): k for k in mapping.keys()}
    db_lower = {normalize(k): k for k in db_teams}
    
    # A. Tim match yang ada di mapping
    match_in_mapping = 0
    match_in_db = 0
    match_not_found = []
    
    for t in match_teams:
        t_lower = normalize(t)
        
        # Cek di mapping
        found_mapping = False
        for mk in mapping_lower:
            if mk == t_lower or (len(mk) >= 5 and len(t_lower) >= 5 and (mk in t_lower or t_lower in mk)):
                found_mapping = True
                break
        
        # Cek di DB
        found_db = t_lower in db_lower
        
        if found_mapping:
            match_in_mapping += 1
        else:
            match_not_found.append(t)
        
        if found_db:
            match_in_db += 1
    
    print(f"\n📊 Tim match hari ini: {len(match_teams)}")
    print(f"   ✅ Ada di mapping: {match_in_mapping} ({match_in_mapping/len(match_teams)*100:.1f}%)")
    print(f"   ✅ Ada di database: {match_in_db} ({match_in_db/len(match_teams)*100:.1f}%)")
    print(f"   ❌ Tidak ada mapping: {len(match_not_found)}")
    
    if match_not_found:
        print(f"\n   ⚠️ Tim tanpa mapping (contoh):")
        for t in sorted(match_not_found)[:20]:
            print(f"      - {t}")
    
    # B. Coverage liga
    print(f"\n📊 Coverage per liga (match hari ini):")
    liga_stats = {}
    for m in matches:
        liga = m.get("liga", "?")
        if liga not in liga_stats:
            liga_stats[liga] = {"total": 0, "in_mapping": 0}
        liga_stats[liga]["total"] += 1
        
        # Cek home & away
        for t in [m.get("home"), m.get("away")]:
            if not t: continue
            t_lower = normalize(t)
            for mk in mapping_lower:
                if mk == t_lower or (len(mk) >= 5 and len(t_lower) >= 5 and (mk in t_lower or t_lower in mk)):
                    liga_stats[liga]["in_mapping"] += 1
                    break
    
    for liga, st in sorted(liga_stats.items()):
        total_tim = st["total"] * 2
        cov = st["in_mapping"] / total_tim * 100 if total_tim > 0 else 0
        emoji = "✅" if cov >= 80 else "🟡" if cov >= 50 else "❌"
        print(f"   {emoji} {liga[:40]:40} {st['in_mapping']}/{total_tim} ({cov:.0f}%)")
    
    # C. Simpan hasil
    hasil = {
        "total_db_teams": len(db_teams),
        "total_mapping": len(mapping),
        "total_match_teams": len(match_teams),
        "match_in_mapping": match_in_mapping,
        "match_in_db": match_in_db,
        "match_not_found": sorted(match_not_found),
    }
    
    with open("output/audit_team.json", "w", encoding="utf-8") as f:
        json.dump(hasil, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Disimpan: output/audit_team.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
