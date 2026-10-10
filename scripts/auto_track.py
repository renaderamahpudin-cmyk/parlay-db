"""
AUTO-TRACK RECORD — Update hasil match via Fotmob
Fokus: 8 liga yang sudah di-mapping
"""
import json
import os
import requests
import pandas as pd
from datetime import datetime

MAPPING_FILE = "output/mapping_liga.json"
PICK_FILE = "output/best_pick.json"
TRACK_FILE = "output/track_record.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}


def load_mapping():
    with open(MAPPING_FILE) as f:
        return json.load(f)


def load_picks():
    with open(PICK_FILE) as f:
        return json.load(f)


import unicodedata

# Prefix/suffix umum yang bisa dibuang
KATA_UMUM = [
    "fc", "sc", "ac", "afc", "cf", "cd", "sk", "ik", "fk", "if",
    "sv", "bv", "rc", "as", "ss", "us", "ssc", "fk", "kf",
    "united", "utd", "city", "town", "club", "de", "cf",
]

# Alias khusus (web → fotmob)
ALIAS_KHUSUS = {
    "gais goteborg": "gais",
    "ik sirius fk": "sirius",
    "caykur rizespor": "rizespor",
    "wsg tirol": "wsg tirol",
    "sv ried": "ried",
    "maritimo": "maritimo",
    # Mexico
    "guadalajara chivas": "chivas",
    "guadalajara": "chivas",
    "cd guadalajara": "chivas",
}


def normalize_nama(nama):
    """Normalisasi nama tim"""
    if not nama:
        return ""
    
    # 1. Lowercase
    n = nama.lower().strip()
    
    # 2. Buang aksen (í → i, ç → c, ö → o)
    n = unicodedata.normalize("NFKD", n)
    n = "".join(c for c in n if not unicodedata.combining(c))
    
    # 3. Buang tanda baca
    n = n.replace(".", " ").replace("-", " ").replace("'", "")
    n = " ".join(n.split())
    
    return n


def normalize_buang_umum(nama):
    """Normalisasi + buang kata umum"""
    n = normalize_nama(nama)
    words = [w for w in n.split() if w not in KATA_UMUM]
    return " ".join(words)


def fuzzy_match(nama_a, nama_b):
    """Cek apakah 2 nama tim cocok (dengan normalisasi + alias)"""
    if not nama_a or not nama_b:
        return False
    
    # 1. Cek alias khusus dulu
    a_raw = normalize_nama(nama_a)
    b_raw = normalize_nama(nama_b)
    
    if a_raw in ALIAS_KHUSUS and ALIAS_KHUSUS[a_raw] == b_raw:
        return True
    if b_raw in ALIAS_KHUSUS and ALIAS_KHUSUS[b_raw] == a_raw:
        return True
    
    # 2. Normalisasi
    a = normalize_nama(nama_a)
    b = normalize_nama(nama_b)
    
    # Exact match
    if a == b:
        return True
    
    # 3. Normalisasi + buang kata umum
    a2 = normalize_buang_umum(nama_a)
    b2 = normalize_buang_umum(nama_b)
    
    if a2 and b2 and a2 == b2:
        return True
    
    # 4. Substring check (min 4 char)
    if len(a2) >= 4 and len(b2) >= 4:
        if a2 in b2 or b2 in a2:
            # Cek selisih panjang max 50%
            diff = abs(len(a2) - len(b2))
            if diff <= max(len(a2), len(b2)) * 0.5:
                return True
    
    return False


def fetch_liga_fixtures(liga_id):
    """Ambil semua match dari 1 liga"""
    url = f"https://www.fotmob.com/api/data/leagues?id={liga_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("fixtures", {}).get("allMatches", [])
    except:
        return []


def cari_match_di_fixtures(fixtures, home_target, away_target):
    """Cari match yang cocok"""
    for m in fixtures:
        home_f = m.get("home", {}).get("name", "")
        away_f = m.get("away", {}).get("name", "")
        
        if fuzzy_match(home_target, home_f) and fuzzy_match(away_target, away_f):
            return m
    return None


def tentukan_hasil(pick, total_gol, skor_home, skor_away, odds):
    """Tentukan WIN/LOSE/PUSH"""
    if "OVER" in pick:
        line = float(pick.replace("OVER ", ""))
        if total_gol > line:
            return "WIN", round(odds - 1, 2)
        elif total_gol == line:
            return "PUSH", 0
        else:
            return "LOSE", -1
    
    elif "UNDER" in pick:
        line = float(pick.replace("UNDER ", ""))
        if total_gol < line:
            return "WIN", round(odds - 1, 2)
        elif total_gol == line:
            return "PUSH", 0
        else:
            return "LOSE", -1
    
    elif pick == "HOME":
        if skor_home > skor_away:
            return "WIN", round(odds - 1, 2)
        else:
            return "LOSE", -1
    
    elif pick == "AWAY":
        if skor_away > skor_home:
            return "WIN", round(odds - 1, 2)
        else:
            return "LOSE", -1
    
    return "?", 0


def main():
    mapping = load_mapping()
    picks = load_picks()
    
    print("=" * 70)
    print("🔍 AUTO-TRACK RECORD")
    print("=" * 70)
    print(f"Total pick: {len(picks)}")
    print(f"Liga di mapping: {len(mapping)}")
    
    # Filter pick yang liga-nya ada di mapping
    picks_valid = [p for p in picks if p["liga"] in mapping]
    picks_skip = [p for p in picks if p["liga"] not in mapping]
    
    print(f"\n✅ Lolos (liga di mapping): {len(picks_valid)}")
    print(f"❌ Skip (liga nggak ada): {len(picks_skip)}")
    
    # Load track record
    if os.path.exists(TRACK_FILE):
        df_track = pd.read_csv(TRACK_FILE)
    else:
        df_track = pd.DataFrame(columns=[
            "tanggal", "liga", "home", "away", "pick", "conf", "odds",
            "skor_home", "skor_away", "total_gol", "hasil", "profit_loss"
        ])
    
    # Cek sudah ada di track?
    existing = set()
    if len(df_track) > 0:
        existing = set(zip(df_track["home"], df_track["away"]))
    
    # Fetch per liga
    liga_cache = {}
    found = 0
    not_finished = 0
    not_found = 0
    
    print("\n" + "=" * 70)
    
    for p in picks_valid:
        home = p["home"]
        away = p["away"]
        liga = p["liga"]
        liga_id = mapping[liga]["id"]
        
        # Skip kalau sudah ada di track
        if (home, away) in existing:
            print(f"⏭️  SKIP (sudah ditrack): {home} vs {away}")
            continue
        
        # Fetch liga (cache)
        if liga_id not in liga_cache:
            print(f"📥 Fetch liga {liga}...")
            liga_cache[liga_id] = fetch_liga_fixtures(liga_id)
        
        fixtures = liga_cache[liga_id]
        
        # Cari match
        m = cari_match_di_fixtures(fixtures, home, away)
        
        if m is None:
            print(f"❌ NOT FOUND: {home} vs {away} ({liga})")
            not_found += 1
            continue
        
        # Cek status
        status = m.get("status", {})
        finished = status.get("finished", False)
        score_str = status.get("scoreStr", "")
        
        if not finished or not score_str:
            print(f"⏳ BELUM: {home} vs {away} — {status.get('reason', {}).get('short', '?')}")
            not_finished += 1
            continue
        
        # Parse skor
        try:
            parts = score_str.replace(" ", "").split("-")
            skor_home = int(parts[0])
            skor_away = int(parts[1])
            total_gol = skor_home + skor_away
        except:
            print(f"⚠️ Parse error: {score_str}")
            continue
        
        # Tentukan hasil
        pick = p.get("pick", "")
        odds = p.get("pick_odds", 0) or p.get("odds", 0)
        hasil, profit = tentukan_hasil(pick, total_gol, skor_home, skor_away, odds)
        
        # Simpan
        row = {
            "tanggal": datetime.now().strftime("%Y-%m-%d"),
            "liga": liga,
            "home": home,
            "away": away,
            "pick": pick,
            "conf": p.get("pick_conf", 0),
            "odds": odds,
            "skor_home": skor_home,
            "skor_away": skor_away,
            "total_gol": total_gol,
            "hasil": hasil,
            "profit_loss": profit,
        }
        df_track = pd.concat([df_track, pd.DataFrame([row])], ignore_index=True)
        found += 1
        
        emoji = "✅" if hasil == "WIN" else "❌" if hasil == "LOSE" else "⚖️"
        print(f"{emoji} {home} {skor_home}-{skor_away} {away} — {pick} → {hasil} ({profit:+.2f})")
    
    # Simpan
    df_track.to_csv(TRACK_FILE, index=False)
    
    print("\n" + "=" * 70)
    print(f"✅ Ditrack: {found}")
    print(f"⏳ Belum selesai: {not_finished}")
    print(f"❌ Tidak ditemukan: {not_found}")
    print(f"💾 File: {TRACK_FILE}")
    print("=" * 70)
    
    # Summary kalau ada data
    if len(df_track) > 0:
        total = len(df_track)
        win = len(df_track[df_track["hasil"] == "WIN"])
        lose = len(df_track[df_track["hasil"] == "LOSE"])
        push = len(df_track[df_track["hasil"] == "PUSH"])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total: {total}")
        print(f"   ✅ Win: {win} ({win/total*100:.1f}%)")
        print(f"   ❌ Lose: {lose} ({lose/total*100:.1f}%)")
        print(f"   ⚖️  Push: {push} ({push/total*100:.1f}%)")
        print(f"   💰 Total profit: {df_track['profit_loss'].sum():+.2f}x")


if __name__ == "__main__":
    main()
