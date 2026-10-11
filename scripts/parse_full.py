"""
Parser lengkap: 1X2 + HDP + O/U
Ambil semua pasar dari mainbolakaki.pro
"""
import warnings
warnings.filterwarnings("ignore")
import json
import re
import requests
import time
import sys
import os

# Path adjustment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)


def fetch_odds():
    """Fetch data dari mainbolakaki.pro"""
    url = "https://mainbolakaki.pro/_view/ParGenWFH.ashx"
    params = {
        "g": "2", "ot": "t", "wd": "", "ia": "0",
        "update": "true", "r": int(time.time())
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
        "Referer": "https://mainbolakaki.pro/_view/odds4.aspx",
    }
    r = requests.get(url, params=params, headers=headers, timeout=15)
    return r.text


def parse_full(raw):
    """Parse semua baris (1X2 + O/U multi-line) per match"""
    try:
        cleaned = raw.strip()
        # Cari posisi array JSON yang valid
        start_idx = cleaned.find("[")
        end_idx = cleaned.rfind("]")
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("Tidak ditemukan format array JSON")
        
        cleaned = cleaned[start_idx:end_idx + 1]
        
        # Parse JSON dengan error handling
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            print("   Coba dengan ast.literal_eval...")
            import ast
            data = ast.literal_eval(cleaned)
    except Exception as e:
        print(f"❌ Parse error: {e}")
        raise ValueError(f"Gagal parse data dari web: {e}")

    ligas_raw = data[3]
    hasil = []

    def ambil_ou(m):
        """Ambil O/U dari 1 baris — coba semua pasangan field"""
        line = None
        
        try:
            v20 = m[20]
            if isinstance(v20, (int, float)) and 1.5 <= v20 <= 10:
                line = float(v20)
        except (IndexError, TypeError):
            return None
        
        if not line:
            return None
        
        # Kandidat pasangan (over_idx, under_idx)
        # Field [29]/[30] sering 10/110 (placeholder) — skip kalau aneh
        kandidat_pasangan = [
            (17, 18),  # baris 2
            (24, 25),  # baris 3
            (29, 30),  # baris 1
        ]
        
        for over_idx, under_idx in kandidat_pasangan:
            try:
                v_over = m[over_idx]
                v_under = m[under_idx]
                
                if not isinstance(v_over, (int, float)) or not isinstance(v_under, (int, float)):
                    continue
                
                # Skip placeholder (10, 110, 0, dll)
                if v_over in (0, 10, 100, 110) or v_under in (0, 10, 100, 110):
                    continue
                
                # Convert ÷10 kalau > 10
                over_v = round(v_over / 10, 2) if v_over > 10 else round(v_over, 2)
                under_v = round(v_under / 10, 2) if v_under > 10 else round(v_under, 2)
                
                # Validasi: odds harus 1.01-20 dan masuk akal
                if 1.01 < over_v < 20 and 1.01 < under_v < 20:
                    return {"line": line, "over": over_v, "under": under_v}
            except (IndexError, TypeError):
                continue
        
        return None

    for liga in ligas_raw:
        if not isinstance(liga, list) or len(liga) < 2:
            continue
        info = liga[0]
        matches = liga[1]
        if not isinstance(info, list) or len(info) < 2:
            continue
        nama_liga = info[1]
        if not isinstance(matches, list):
            continue

        i = 0
        while i < len(matches):
            m = matches[i]
            if not isinstance(m, list) or len(m) < 14:
                i += 1
                continue
            
            try:
                odds_home = m[11]
                odds_draw = m[12]
                odds_away = m[13]

                # Hanya baris 1X2 utama
                if not all(isinstance(x, (int, float)) and x > 1.0
                          for x in [odds_home, odds_draw, odds_away]):
                    i += 1
                    continue

                # Kumpulkan O/U dari 3 baris
                ou_lines = []
                for j in range(3):
                    if i + j >= len(matches):
                        break
                    mj = matches[i + j]
                    if not isinstance(mj, list):
                        continue
                    ou = ambil_ou(mj)
                    if ou:
                        ou_lines.append(ou)

                # Dedup berdasarkan line
                seen = set()
                ou_unique = []
                for ou in ou_lines:
                    key = ou["line"]
                    if key not in seen:
                        seen.add(key)
                        ou_unique.append(ou)

                is_live = "LIVE" in str(m[2]).upper()

                hasil.append({
                    "liga": nama_liga,
                    "waktu": m[4],
                    "home": str(m[6]).strip(),
                    "away": str(m[7]).strip(),
                    "is_live": is_live,
                    "odds_home": float(odds_home),
                    "odds_draw": float(odds_draw),
                    "odds_away": float(odds_away),
                    "ou_lines": ou_unique,
                })
            except Exception:
                pass
            
            i += 3

    # Dedup match
    seen = {}
    dedup = []
    for m in hasil:
        key = (m["home"].lower(), m["away"].lower())
        if key not in seen:
            seen[key] = m
            dedup.append(m)

    return dedup

def main():
    print("=" * 70)
    print("PARSE FULL — 1X2 + O/U")
    print("=" * 70)

    print("\n[1] Fetch dari mainbolakaki.pro...")
    try:
        raw = fetch_odds()
        print(f"    ✅ {len(raw):,} karakter")
    except Exception as e:
        print(f"    ❌ {e} — pakai file lokal")
        try:
            with open("pargen_raw.html", "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read()
        except FileNotFoundError:
            print(f"    ❌ File lokal juga tidak ditemukan")
            return []

    print("\n[2] Parse...")
    try:
        matches = parse_full(raw)
        print(f"    ✅ {len(matches)} match unik (setelah dedup)")
    except Exception as e:
        print(f"    ❌ Parse gagal: {e}")
        return []

    # Simpan
    os.makedirs("output", exist_ok=True)
    with open("output/match_full.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)
    print(f"    💾 Disimpan: output/match_full.json")

    return matches


if __name__ == "__main__":
    main()
