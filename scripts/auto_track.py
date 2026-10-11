"""
AUTO-TRACK RECORD — Update hasil match via Fotmob
Fokus: 8 liga yang sudah di-mapping
"""
import json
import os
import requests
import pandas as pd
from datetime import datetime
import re

from pick_policy import is_eligible_ou_pick, is_over_under_pick
from settlement import TRACK_COLUMNS, match_key, settle_pick

MAPPING_FILE = "output/mapping_liga.json"
PICK_FILE = "output/best_pick.json"
TRACK_FILE = "output/track_record.csv"
DRAFT_FILE = "output/draft_pending.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}


def load_mapping():
    with open(MAPPING_FILE) as f:
        return json.load(f)


def load_picks():
    pending = None
    if os.path.exists(DRAFT_FILE):
        with open(DRAFT_FILE, encoding="utf-8") as f:
            draft = json.load(f)
        pending = draft.get("pending_auto")
        if not isinstance(pending, list):
            raise ValueError(f"Format {DRAFT_FILE} tidak memiliki pending_auto berupa list.")
        pending = [item for item in pending if is_over_under_pick(item)]

    if not os.path.exists(PICK_FILE):
        if pending is not None:
            return pending
        raise FileNotFoundError(f"File pick tidak ditemukan: {PICK_FILE}")
    with open(PICK_FILE, encoding="utf-8") as f:
        latest_picks = json.load(f)

    if pending is None:
        return [item for item in latest_picks if is_eligible_ou_pick(item)]

    # Lengkapi draft lama yang belum menyimpan odds/confidence tanpa mengganti
    # pilihan historisnya dengan pick baru yang berbeda.
    latest_by_key = {}
    for item in latest_picks:
        if not is_eligible_ou_pick(item):
            continue
        key = (*match_key(item.get("liga"), item.get("home"), item.get("away")),
               str(item.get("waktu", "")).strip(),
               str(item.get("pick", "")).strip().upper())
        latest_by_key[key] = item
    fields_to_recover = (
        "pick_conf", "pick_odds", "pick_implied", "pick_alasan",
        "value_gap", "kategori_gap", "skor", "tier", "pick_push_rate",
    )
    for item in pending:
        key = (*match_key(item.get("liga"), item.get("home"), item.get("away")),
               str(item.get("waktu", "")).strip(),
               str(item.get("pick", "")).strip().upper())
        latest = latest_by_key.get(key)
        if latest:
            for field in fields_to_recover:
                if item.get(field) in (None, "") and field in latest:
                    item[field] = latest[field]
    return pending


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
        r.raise_for_status()
        data = r.json()
        fixtures = data.get("fixtures", {}).get("allMatches")
        if not isinstance(fixtures, list):
            return None
        return fixtures
    except (requests.RequestException, ValueError, AttributeError):
        return None


def cari_match_di_fixtures(fixtures, home_target, away_target):
    """Cari match yang cocok"""
    for m in fixtures:
        home_f = m.get("home", {}).get("name", "")
        away_f = m.get("away", {}).get("name", "")
        
        if fuzzy_match(home_target, home_f) and fuzzy_match(away_target, away_f):
            return m
    return None


def tentukan_hasil(pick, total_gol, skor_home, skor_away, odds):
    """Tentukan hasil O/U Asia atau 1X2, termasuk DRAW dan half-result."""
    return settle_pick(pick, skor_home, skor_away, odds)


def tanggal_match(status):
    """Ambil tanggal fixture dari waktu FotMob; fallback ke tanggal pencatatan."""
    utc_time = status.get("utcTime")
    if utc_time:
        try:
            return datetime.fromisoformat(
                utc_time.replace("Z", "+00:00")
            ).date().isoformat()
        except (AttributeError, TypeError, ValueError):
            pass
    return datetime.now().strftime("%Y-%m-%d")


def hapus_draft_selesai(completed_keys):
    """Hapus pick dari antrean hanya setelah hasilnya sudah tercatat."""
    if not os.path.exists(DRAFT_FILE):
        return
    try:
        with open(DRAFT_FILE, encoding="utf-8") as f:
            draft = json.load(f)
        pending = draft.get("pending_auto", [])
        draft["pending_auto"] = [
            item for item in pending
            if match_key(item.get("liga"), item.get("home"), item.get("away"))
            not in completed_keys
        ]
        draft["total_pending_auto"] = len(draft["pending_auto"])
        draft["saved_at"] = datetime.now().isoformat()
        tmp_file = f"{DRAFT_FILE}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, DRAFT_FILE)
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        print(f"⚠️ Draft belum bisa diperbarui: {exc}")


def main():
    mapping = load_mapping()
    picks = load_picks()
    
    print("=" * 70)
    print("🔍 AUTO-TRACK RECORD")
    print("=" * 70)
    print(f"Total pick: {len(picks)}")
    print(f"Liga di mapping: {len(mapping)}")
    
    # Filter pick yang liga-nya ada di mapping
    picks_valid = [p for p in picks if p.get("liga") in mapping]
    picks_skip = [p for p in picks if p.get("liga") not in mapping]
    
    print(f"\n✅ Lolos (liga di mapping): {len(picks_valid)}")
    print(f"❌ Skip (liga nggak ada): {len(picks_skip)}")
    
    # Load track record
    if os.path.exists(TRACK_FILE):
        df_track = pd.read_csv(TRACK_FILE)
    else:
        df_track = pd.DataFrame(columns=TRACK_COLUMNS)
    for column in TRACK_COLUMNS:
        if column not in df_track.columns:
            df_track[column] = pd.NA
    
    # Kunci memasukkan liga agar nama tim sama di kompetisi berbeda tidak tabrakan.
    existing = {
        match_key(row.liga, row.home, row.away)
        for row in df_track[["liga", "home", "away"]].itertuples(index=False)
        if pd.notna(row.home) and pd.notna(row.away)
    }
    completed_keys = set(existing)
    
    # Fetch per liga
    liga_cache = {}
    found = 0
    not_finished = 0
    not_found = 0
    fetch_failed = 0
    invalid_pick = 0
    
    print("\n" + "=" * 70)
    
    for p in picks_valid:
        home = p.get("home", "")
        away = p.get("away", "")
        liga = p.get("liga", "")
        fixture_key = match_key(liga, home, away)
        liga_id = mapping[liga]["id"]
        
        # Skip kalau sudah ada di track
        if fixture_key in existing:
            print(f"⏭️  SKIP (sudah ditrack): {home} vs {away}")
            continue
        
        # Fetch liga (cache)
        if liga_id not in liga_cache:
            print(f"📥 Fetch liga {liga}...")
            liga_cache[liga_id] = fetch_liga_fixtures(liga_id)
        
        fixtures = liga_cache[liga_id]
        if fixtures is None:
            print(f"⚠️ FETCH GAGAL: {liga}; pick tetap tersimpan untuk dicoba lagi.")
            fetch_failed += 1
            continue
        
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
        score_match = re.fullmatch(r"\s*(\d+)\s*[-–]\s*(\d+)\s*", str(score_str))
        if not score_match:
            print(f"⚠️ Parse error: {score_str}")
            continue
        skor_home = int(score_match.group(1))
        skor_away = int(score_match.group(2))
        total_gol = skor_home + skor_away
        
        # Tentukan hasil
        pick = p.get("pick", "")
        odds = p.get("pick_odds") or p.get("odds")
        try:
            hasil, profit = tentukan_hasil(
                pick, total_gol, skor_home, skor_away, odds
            )
        except (TypeError, ValueError) as exc:
            print(f"⚠️ Pick tidak bisa dihitung untuk {home} vs {away}: {exc}")
            invalid_pick += 1
            continue
        
        # Simpan
        row = {
            "tanggal": tanggal_match(status),
            "liga": liga,
            "home": home,
            "away": away,
            "pick": pick,
            "conf": p.get("pick_conf", 0),
            "odds": odds,
            "skor": p.get("skor", 0),
            "tier": p.get("tier", "?"),
            "pick_push_rate": p.get("pick_push_rate", 0),
            "skor_home": skor_home,
            "skor_away": skor_away,
            "total_gol": total_gol,
            "hasil": hasil,
            "profit_loss": profit,
            "catatan": "",
        }
        df_track = pd.concat([
            df_track, pd.DataFrame([row], columns=TRACK_COLUMNS)
        ], ignore_index=True)
        existing.add(fixture_key)
        completed_keys.add(fixture_key)
        found += 1
        
        emoji = (
            "✅" if hasil in {"WIN", "HALF_WIN"}
            else "❌" if hasil in {"LOSE", "HALF_LOSE"}
            else "⚖️"
        )
        print(f"{emoji} {home} {skor_home}-{skor_away} {away} — {pick} → {hasil} ({profit:+.2f})")
    
    # Simpan
    df_track = df_track[TRACK_COLUMNS]
    df_track.to_csv(TRACK_FILE, index=False)
    hapus_draft_selesai(completed_keys)
    
    print("\n" + "=" * 70)
    print(f"✅ Ditrack: {found}")
    print(f"⏳ Belum selesai: {not_finished}")
    print(f"❌ Tidak ditemukan: {not_found}")
    print(f"⚠️ Fetch gagal: {fetch_failed}")
    print(f"⚠️ Pick tidak valid/tidak ada odds: {invalid_pick}")
    print(f"💾 File: {TRACK_FILE}")
    print("=" * 70)
    
    # Summary kalau ada data
    if len(df_track) > 0:
        total = len(df_track)
        result_counts = df_track["hasil"].value_counts()
        print(f"\n📊 SUMMARY:")
        print(f"   Total: {total}")
        for result, label in (
            ("WIN", "✅ Menang"),
            ("HALF_WIN", "🟢 Menang setengah"),
            ("LOSE", "❌ Kalah"),
            ("HALF_LOSE", "🟠 Kalah setengah"),
            ("PUSH", "⚖️ Push"),
        ):
            count = int(result_counts.get(result, 0))
            print(f"   {label}: {count} ({count/total*100:.1f}%)")
        print(f"   💰 Total profit: {df_track['profit_loss'].sum():+.2f}x")


if __name__ == "__main__":
    main()
