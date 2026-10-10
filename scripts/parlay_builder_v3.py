"""
Parlay Builder v3 — BEST PICK
Pilih 1 rekomendasi terbaik per match (1X2 / O/U / BTTS)
"""
import warnings
warnings.filterwarnings("ignore")
import json
import pandas as pd
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from settlement import settle_pick
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# ========== KONFIGURASI ==========
MIN_H2H = 5
MIN_HOME = 5
MIN_AWAY = 5
BOBOT_H2H = 10
BOBOT_HOME = 5
BOBOT_AWAY = 5
MODAL = 100_000

MIN_CONF_PICK = 60     # naikkan dari 65 (backtest: 60%+ win)
MIN_ODDS = 1.20        # naikkan dari 1.30
MAX_ODDS = 4.00

# Liga profitable (whitelist)
LIGA_WHITELIST = [
    "Primeira Liga", "Norway Eliteserien", "Serie A", "La Liga",
    "Eredivisie", "Sweden Allsvenskan", "Denmark Superliga",
    "Finland Veikkausliiga", "Ireland Premier Division",
    "Japan J-League", "Brazil Serie A",
    "Championship", "Bundesliga", "Ligue 1",
]

MIN_CONF_PICK = 60     # naikkan dari 65 (backtest: 60%+ win)
MIN_ODDS = 1.20        # naikkan dari 1.30
MAX_ODDS = 4.00

# Liga profitable (whitelist)
LIGA_WHITELIST = [
    "Primeira Liga", "Norway Eliteserien", "Serie A", "La Liga",
    "Eredivisie", "Sweden Allsvenskan", "Denmark Superliga",
    "Finland Veikkausliiga", "Ireland Premier Division",
    "Japan J-League", "Brazil Serie A",
    "Championship", "Bundesliga", "Ligue 1",
]

# Threshold confidence minimum untuk BEST PICK
MIN_CONF_PICK = 60


# ========== ALIAS TIM ==========
ALIAS = {
    "hjk helsinki": ["hjk", "hjk helsinki", "helsinki"],
    "vaasa vps": ["vps", "vaasa", "vaasan"],
    "kups": ["kups", "kuopio"],
    "ac oulu": ["oulu", "ac oulu"],
    "shamrock rovers": ["shamrock", "shamrock rovers"],
    "drogheda united": ["drogheda", "drogheda united"],
    "santos sp": ["santos"],
    "flamengo rj": ["flamengo"],
    "fluminense rj": ["fluminense"],
    "coritiba pr": ["coritiba"],
    "palmeiras sp": ["palmeiras"],
    "bahia ec ba": ["bahia"],
    "ceara ce": ["ceara"],
    "criciuma ec sc": ["criciuma"],
    "nautico pe": ["nautico"],
    "gremio novorizontino sp": ["novorizontino", "gremio novorizontino"],
    "atletico fc": ["atletico"],
    "real cartagena": ["cartagena"],
    "independiente valle del cauca": ["independiente"],
    "tigres fc": ["tigres"],
}


def normalize(name):
    if not isinstance(name, str):
        return ""
    return re.sub(r'\s*\[[RW]\]\s*', '', name.strip()).lower()


def load_h2h():
    data = []
    try:
        df = pd.read_csv("data/football_data/all_football_data.csv", low_memory=False)
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
        df = df[["HomeTeam", "AwayTeam", "FTHG", "FTAG", "League"]].copy()
        df.columns = ["home", "away", "hg", "ag", "league"]
        df["source"] = "top"
        data.append(df)
    except Exception:
        pass
    try:
        df = pd.read_csv("data/football_data_extra/all_extra.csv", low_memory=False)
        df = df.dropna(subset=["Home", "Away", "HG", "AG"])
        liga_col = "LeagueName" if "LeagueName" in df.columns else "League"
        df = df[["Home", "Away", "HG", "AG", liga_col]].copy()
        df.columns = ["home", "away", "hg", "ag", "league"]
        df["source"] = "extra"
        data.append(df)
    except Exception:
        pass
    df = pd.concat(data, ignore_index=True)
    df["hg"] = pd.to_numeric(df["hg"], errors="coerce")
    df["ag"] = pd.to_numeric(df["ag"], errors="coerce")
    return df.dropna(subset=["hg", "ag"])


def cari_h2h(df, home_web, away_web):
    def get_aliases(nama):
        n = normalize(nama)
        return ALIAS.get(n, [n])

    home_aliases = get_aliases(home_web)
    away_aliases = get_aliases(away_web)

    def match_any(nama_db, aliases):
        n = normalize(nama_db)
        if not n:
            return False
        for alias in aliases:
            if alias == n:
                return True
            if len(alias) >= 4 and len(n) >= 4:
                if alias in n or n in alias:
                    if abs(len(n) - len(alias)) <= max(len(alias), 3):
                        return True
        return False

    mask = (
        (df["home"].apply(lambda x: match_any(x, home_aliases)) &
         df["away"].apply(lambda x: match_any(x, away_aliases))) |
        (df["home"].apply(lambda x: match_any(x, away_aliases)) &
         df["away"].apply(lambda x: match_any(x, home_aliases)))
    )
    return df[mask].copy()


def analisa(h2h, home_web, away_web, odds_home=0, odds_draw=0, odds_away=0,
            ou_lines=None):
    if ou_lines is None:
        ou_lines = []
    if len(h2h) < MIN_H2H:
        return None

    home_norm = normalize(home_web)

    def is_home(row):
        n = normalize(row["home"])
        return n == home_norm or (len(home_norm) >= 5 and home_norm in n)

    h2h = h2h.copy()
    h2h["home_is_A"] = h2h.apply(is_home, axis=1)
    home_a = h2h["home_is_A"].sum()
    home_b = len(h2h) - home_a

    def hasil(row):
        if row["home_is_A"]:
            h, a = row["hg"], row["ag"]
        else:
            h, a = row["ag"], row["hg"]
        if h > a: return "W"
        elif h < a: return "L"
        return "D"

    h2h["hasil_a"] = h2h.apply(hasil, axis=1)
    menang_a = (h2h["hasil_a"] == "W").sum()
    draw = (h2h["hasil_a"] == "D").sum()
    menang_b = (h2h["hasil_a"] == "L").sum()

    def gol(row):
        if row["home_is_A"]:
            return row["hg"], row["ag"]
        return row["ag"], row["hg"]

    gol_pairs = h2h.apply(gol, axis=1)
    gol_a = [g[0] for g in gol_pairs]
    gol_b = [g[1] for g in gol_pairs]

    avg_a = sum(gol_a) / len(gol_a)
    avg_b = sum(gol_b) / len(gol_b)
    avg_total = avg_a + avg_b

    win_rate = (menang_a / len(h2h)) * 100
    draw_rate = (draw / len(h2h)) * 100

    # ===== BTTS rate =====
    btts_count = sum(1 for g in gol_pairs if g[0] > 0 and g[1] > 0)
    btts_rate = (btts_count / len(h2h)) * 100

    # ===== Skor =====
    skor = (max(0, len(h2h) - MIN_H2H) * BOBOT_H2H +
            max(0, home_a - MIN_HOME) * BOBOT_HOME +
            max(0, home_b - MIN_AWAY) * BOBOT_AWAY)

    # ===== Kandidat rekomendasi =====
    kandidat = []

    # 1X2
    if win_rate >= 60:
        kandidat.append({
            "jenis": "1X2",
            "pick": "HOME",
            "confidence": min(95, 50 + (win_rate - 50) * 1.5),
            "alasan": f"Home menang {win_rate:.0f}% dari H2H",
        })
    elif win_rate <= 30:
        kandidat.append({
            "jenis": "1X2",
            "pick": "AWAY",
            "confidence": min(95, 50 + (30 - win_rate) * 1.5),
            "alasan": f"Away menang {100-win_rate:.0f}% dari H2H",
        })

    # O/U — hanya kalau gol total JELAS
    # O/U — pakai probabilitas gol aktual (bukan estimasi)
    total_goals_list = [g[0] + g[1] for g in gol_pairs]
    if len(total_goals_list) > 0:
        over_25_count = sum(1 for g in total_goals_list if g > 2.5)
        over_25_rate = (over_25_count / len(total_goals_list)) * 100
        under_25_rate = 100 - over_25_rate
        
        if over_25_rate >= 55:
            kandidat.append({
                "jenis": "OU",
                "pick": "OVER 2.5",
                "confidence": round(over_25_rate, 1),
                "alasan": f"Over 2.5: {over_25_rate:.0f}% dari H2H",
            })
        elif under_25_rate >= 55:
            kandidat.append({
                "jenis": "OU",
                "pick": "UNDER 2.5",
                "confidence": round(under_25_rate, 1),
                "alasan": f"Under 2.5: {under_25_rate:.0f}% dari H2H",
            })


    # BTTS
    if btts_rate >= 65:
        kandidat.append({
            "jenis": "BTTS",
            "pick": "BTTS YES",
            "confidence": btts_rate,
            "alasan": f"Kedua tim cetak gol {btts_rate:.0f}%",
        })
    elif btts_rate <= 30:
        kandidat.append({
            "jenis": "BTTS",
            "pick": "BTTS NO",
            "confidence": 100 - btts_rate,
            "alasan": f"Cuma 1 tim cetak gol seringnya",
        })

    # ===== MULTI-MARKET PICKER =====
    # Untuk setiap kandidat, hitung Value Gap (confidence vs implied odds)
    # Pilih yang gap positif TERBESAR dengan odds minimal 1.50
    
    MIN_ODDS = 1.20   # naikkan sedikit dari 1.50, karena odds 1.30-1.50 masih OK
    MAX_ODDS = 4.00   # hindari odds terlalu tinggi (kemungkinan data salah)
    
    kandidat_scored = []
    for k in kandidat:
        if k["confidence"] < MIN_CONF_PICK:
            continue
        
        # Ambil odds untuk kandidat ini
        if k["jenis"] == "1X2":
            if k["pick"] == "HOME":
                odds = odds_home
            elif k["pick"] == "AWAY":
                odds = odds_away
            else:
                odds = odds_draw
        elif k["jenis"] == "OU":
            # Pakai odds_real dari kandidat (sudah di-set waktu append)
            if "odds_real" in k and k["odds_real"]:
                odds = k["odds_real"]
            elif "OVER" in k["pick"]:
                odds = 1.90
            else:
                odds = 1.90
        elif k["jenis"] == "BTTS":
            odds = 1.80
        else:
            odds = 1.80
        
        # Skip kalau odds terlalu rendah (trap) atau terlalu tinggi (data salah)
        if odds < MIN_ODDS or odds > MAX_ODDS:
            continue
        
        # Hitung value gap
        implied = 100 / odds
        gap = k["confidence"] - implied
        
        kandidat_scored.append({
            **k,
            "odds": round(odds, 2),
            "implied": round(implied, 1),
            "value_gap": round(gap, 1),
        })
    
    if not kandidat_scored:
        return None
    
    # Sort: value_gap tertinggi dulu, kalau sama → confidence tertinggi
    kandidat_scored.sort(key=lambda x: (-x["value_gap"], -x["confidence"]))
    best = kandidat_scored[0]
    
    # ===== FILTER VALUE GAP =====
    if best["value_gap"] >= 10:
        kategori_gap = "VALUE"
    elif best["value_gap"] >= -10:
        kategori_gap = "FAIR"
    else:
        kategori_gap = "TRAP"
    
    # Skip TRAP
    if kategori_gap == "TRAP":
        return None
    
    # Skip VALUE mencurigakan (> 40%)
    if best["value_gap"] > 40:
        return None
    
    best["pick_odds"] = best["odds"]
    best["pick_implied"] = best["implied"]
    best["kategori_gap"] = kategori_gap
    
    # Info alternatif pasar
    best["alternatif"] = kandidat_scored[1:4] if len(kandidat_scored) > 1 else []

    # Tier
    if skor >= 400:
        tier = "🔥 T1"
    elif skor >= 250:
        tier = "⚡ T2"
    else:
        tier = "✅ T3"

    # ===== FILTER KUALITAS GANDA (Lapis 4) =====
    sinyal = 0
    sinyal_detail = []
    
    # Sinyal A: Win rate tinggi
    if win_rate >= 60:
        sinyal += 1
        sinyal_detail.append("WinRate")
    
    # Sinyal B: Home advantage kuat
    if home_a >= 12:
        sinyal += 1
        sinyal_detail.append("HomeKuat")
    
    # Sinyal C: Away konsisten
    if home_b >= 12:
        sinyal += 1
        sinyal_detail.append("AwayKuat")
    
    # Sinyal D: Skor H2H tinggi
    if skor >= 250:
        sinyal += 1
        sinyal_detail.append("SkorTinggi")
    
    # Harus minimal 2 sinyal
    if sinyal < 1:
        return None
    
    # ===== VALUE COMPARISON =====
    # VALUE COMPARISON (tanpa try/except untuk debug)
    value_comparison = bandingkan_opsi(
        gol_pairs=gol_pairs,
        ou_lines=ou_lines,
        odds_home=odds_home,
        odds_draw=odds_draw,
        odds_away=odds_away,
        home_win_rate=win_rate,
        away_win_rate=(100 - win_rate - draw_rate),
        draw_rate=draw_rate,
    )

    # ===== 2 OPSI (UTAMA + ALTERNATIF) =====
    top_1x2, top_ou, titik_buta = None, None, None
    try:
        top_1x2, top_ou, titik_buta = bandingkan_opsi_2(
            gol_pairs=gol_pairs,
            ou_lines=ou_lines,
            odds_home=odds_home,
            odds_draw=odds_draw,
            odds_away=odds_away,
            home_win_rate=win_rate,
            away_win_rate=(100 - win_rate - draw_rate),
            draw_rate=draw_rate,
        )
    except Exception as e:
        top_1x2, top_ou, titik_buta = None, None, None

    non_loss_rate = win_rate + draw_rate
    
    return {
        "h2h": len(h2h),
        "gol_pairs": [tuple(g) for g in gol_pairs],
        "win_rate": round(win_rate, 1),
        "draw_rate": round(draw_rate, 1),
        "non_loss_rate": round(non_loss_rate, 1),
        "gol_total": round(avg_total, 2),
        "btts_rate": round(btts_rate, 1),
        "skor": int(skor),
        "tier": tier,
        "pick_jenis": best["jenis"],
        "pick": best["pick"],
        "pick_conf": round(best["confidence"], 1),
        "pick_alasan": best["alasan"],
        "pick_odds": best.get("pick_odds"),
        "pick_implied": best.get("pick_implied"),
        "value_gap": best.get("value_gap"),
        "kategori_gap": best.get("kategori_gap"),
        "sinyal": sinyal,
        "sinyal_detail": sinyal_detail,
        "top_1x2": top_1x2,
        "top_ou": top_ou,
        "titik_buta": titik_buta,
        "value_comparison": value_comparison,
        "semua_kandidat": kandidat,
    }



# ========== EVENT LABEL ==========
def cek_event_label(pick):
    """Cek apakah pick cocok untuk event (per pick)."""
    events = []
    jenis = pick.get("pick_jenis", "")
    odds = pick.get("pick_odds", 0)

    # Event Over Under: khusus O/U, min odds 1.75
    if jenis == "OU" and odds >= 1.75:
        events.append("Over Under")

    # Event Parlay Rakyat/Emas: 1X2/OU/BTTS, min 1.77
    if jenis in ("1X2", "OU", "BTTS") and odds >= 1.77:
        events.append("Parlay Rakyat")
        events.append("Parlay Emas")

    # Event Hemat/Mantap: 1X2/OU/BTTS, min 1.75
    if jenis in ("1X2", "OU", "BTTS") and odds >= 1.75:
        events.append("Hemat")
        events.append("Mantap")

    return events


# ========== KUOTA EVENT ==========
EVENT_KUOTA = {
    "Over Under": {"min": 5, "max": 10},
    "Parlay Rakyat": {"min": 6, "max": 10},
    "Parlay Emas": {"min": 6, "max": 10},
    "Hemat": {"min": 5, "max": 5, "exact": True},
    "Mantap": {"min": 7, "max": 10},
}


def hitung_event_tersedia(hasil):
    """Hitung berapa pick per event."""
    count = {}
    for m in hasil:
        events = cek_event_label(m)
        for e in events:
            count[e] = count.get(e, 0) + 1
    return count


def event_layak(event_name, jumlah):
    """Cek apakah event layak ditampilkan."""
    if event_name not in EVENT_KUOTA:
        return False
    kuota = EVENT_KUOTA[event_name]
    
    # Kalau exact, jumlah harus tepat
    if kuota.get("exact"):
        return jumlah == kuota["min"]
    
    return kuota["min"] <= jumlah <= kuota["max"]



# ========== FUNGSI O/U TITIK AMAN ==========
def cari_titik_aman_ou(avg_total, h2h_gols):
    """Cari titik aman O/U berdasarkan distribusi gol H2H."""
    if not h2h_gols or len(h2h_gols) == 0:
        return []
    
    total = len(h2h_gols)
    lines_cek = [1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5]
    hasil = []
    
    for line in lines_cek:
        over_count = sum(1 for g in h2h_gols if g > line)
        over_rate = (over_count / total) * 100
        if over_rate >= 70:
            hasil.append({
                "line": line,
                "over_rate": round(over_rate, 1),
                "pick": f"OVER {line}",
            })
    
    return hasil



# ========== FASE 2: DATA CEDERA ==========
import os as _os
import json as _json
import requests as _requests

# Load mapping tim (kalau ada)
_TEAM_IDS = {}
if _os.path.exists("scripts/team_ids.json"):
    with open("scripts/team_ids.json", "r", encoding="utf-8") as _f:
        _TEAM_IDS = _json.load(_f)
elif _os.path.exists("team_ids.json"):
    with open("team_ids.json", "r", encoding="utf-8") as _f:
        _TEAM_IDS = _json.load(_f)

_CEDERA_CACHE_DIR = "scripts/cache_cedera" if _os.path.exists("scripts/cache_cedera") else "cache_cedera"
_os.makedirs(_CEDERA_CACHE_DIR, exist_ok=True)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
    "Accept": "application/json",
}


def cari_id_tim(nama):
    """Cari ID Fotmob dari nama tim. Return (id, nama_db) atau (None, None)."""
    if not nama or not _TEAM_IDS:
        return None, None
    
    nama_lower = nama.lower().strip()
    
    # 1. Exact match
    for team_name, info in _TEAM_IDS.items():
        if team_name.lower() == nama_lower:
            return info["id"], team_name
    
    # 2. Cek sebagian (fuzzy ketat)
    best_id = None
    best_name = None
    best_score = 0
    
    for team_name, info in _TEAM_IDS.items():
        team_lower = team_name.lower()
        if nama_lower in team_lower or team_lower in nama_lower:
            score = len(nama_lower) / max(len(team_lower), 1)
            if score > best_score:
                best_score = score
                best_id = info["id"]
                best_name = team_name
    
    if best_id and best_score > 0.5:
        return best_id, best_name
    return None, None


def ambil_cedera(team_id):
    """Ambil cedera dari Fotmob dengan cache. Return dict atau None."""
    if not team_id:
        return None
    
    cache_file = _os.path.join(_CEDERA_CACHE_DIR, f"cedera_{team_id}.json")
    
    # Cek cache
    if _os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception:
            pass
    
    # Fetch dari Fotmob
    try:
        url = f"https://www.fotmob.com/api/data/teams?id={team_id}"
        r = _requests.get(url, headers=_HEADERS, timeout=15)
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
                    ret_lower = ret.lower()
                    if "out for" in ret_lower or "month" in ret_lower:
                        sev = "LAMA"
                    elif "doubtful" in ret_lower:
                        sev = "DOUBTFUL"
                    elif "back in" in ret_lower or "few weeks" in ret_lower:
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
            _json.dump(cache, f, indent=2, ensure_ascii=False)
        
        return cache
    except Exception:
        return None


def dampak_cedera(home_cedera, away_cedera):
    """Hitung dampak cedera. Return (delta_home, info_text)."""
    if not home_cedera and not away_cedera:
        return 0, None
    
    def skor_cidera(cedera):
        if not cedera:
            return 0
        bobot = {"LAMA": 3, "SEDANG": 2, "DOUBTFUL": 1, "RINGAN": 0}
        return sum(bobot.get(c["severity"], 0) for c in cedera.get("cedera", []))
    
    skor_home = skor_cidera(home_cedera)
    skor_away = skor_cidera(away_cedera)
    
    # Delta = away_skor - home_skor
    # Kalau home lebih baik (away lebih terpukul) → delta positif
    delta = skor_away - skor_home
    
    # Info text
    info_parts = []
    if home_cedera:
        from collections import Counter
        c = Counter(x["severity"] for x in home_cedera.get("cedera", []))
        info_parts.append(f"H:{home_cedera['total_cedera']}")
    if away_cedera:
        from collections import Counter
        c = Counter(x["severity"] for x in away_cedera.get("cedera", []))
        info_parts.append(f"A:{away_cedera['total_cedera']}")
    
    info = " | ".join(info_parts) if info_parts else None
    
    return delta, info


# ========== FASE 1.5: VALUE COMPARISON ==========
def _nilai_ou_historis(gol_pairs, side, line, odds):
    """Hitung peluang bersyarat, frekuensi push, dan profit historis O/U."""
    try:
        line_value = float(line)
        odds_value = float(odds)
    except (TypeError, ValueError):
        return None
    if not pd.notna(line_value) or not pd.notna(odds_value) or odds_value <= 1:
        return None

    win_units = 0.0
    loss_units = 0.0
    push_units = 0.0
    profit_total = 0.0
    for home_goals, away_goals in gol_pairs:
        try:
            result, profit = settle_pick(
                f"{side} {line_value}", home_goals, away_goals, odds_value
            )
        except (TypeError, ValueError):
            continue
        profit_total += profit
        if result == "WIN":
            win_units += 1
        elif result == "HALF_WIN":
            win_units += 0.5
            push_units += 0.5
        elif result == "LOSE":
            loss_units += 1
        elif result == "HALF_LOSE":
            loss_units += 0.5
            push_units += 0.5
        else:
            push_units += 1

    decided_units = win_units + loss_units
    if not gol_pairs or decided_units == 0:
        return None

    probability = win_units / decided_units * 100
    return {
        "prob": round(probability, 1),
        "gap": round(probability - (100 / odds_value), 1),
        "push_rate": round(push_units / len(gol_pairs) * 100, 1),
        "expected_profit": round(profit_total / len(gol_pairs), 3),
    }


def bandingkan_opsi(gol_pairs, ou_lines, odds_home, odds_draw, odds_away, 
                    home_win_rate=0, away_win_rate=0, draw_rate=0):
    """
    # Konversi gol_pairs ke list kalau pandas Series
    if hasattr(gol_pairs, "tolist"):
        gol_pairs = gol_pairs.tolist()
    elif gol_pairs is None:
        gol_pairs = []

    Bandingkan semua opsi: 1X2 vs O/U per line.
    Return: list opsi sorted by gap tertinggi.
    """
    # Konversi gol_pairs ke list kalau pandas Series
    if hasattr(gol_pairs, "tolist"):
        gol_pairs = gol_pairs.tolist()
    elif gol_pairs is None:
        gol_pairs = []

    if not gol_pairs or len(gol_pairs) == 0:
        return []
    
    total_gols = [g[0] + g[1] for g in gol_pairs]
    n = len(total_gols)
    opsi = []
    
    # ===== 1X2 =====
    # HOME
    if odds_home and odds_home > 1:
        home_implied = 100 / odds_home
        home_gap = home_win_rate - home_implied
        opsi.append({
            "jenis": "1X2",
            "pick": "HOME",
            "odds": round(odds_home, 2),
            "prob": round(home_win_rate, 1),
            "gap": round(home_gap, 1),
            "line": None,
        })
    
    # DRAW
    if odds_draw and odds_draw > 1:
        draw_implied = 100 / odds_draw
        draw_gap = draw_rate - draw_implied
        opsi.append({
            "jenis": "1X2",
            "pick": "DRAW",
            "odds": round(odds_draw, 2),
            "prob": round(draw_rate, 1),
            "gap": round(draw_gap, 1),
            "line": None,
        })
    
    # AWAY
    if odds_away and odds_away > 1:
        away_implied = 100 / odds_away
        away_gap = away_win_rate - away_implied
        opsi.append({
            "jenis": "1X2",
            "pick": "AWAY",
            "odds": round(odds_away, 2),
            "prob": round(away_win_rate, 1),
            "gap": round(away_gap, 1),
            "line": None,
        })
    
    # ===== O/U per line =====
    if ou_lines:
        for ou in ou_lines:
            line = ou.get("line")
            over_odds = ou.get("over")
            under_odds = ou.get("under")
            
            if line is None:
                continue
            candidates = []
            for side, odds in (("OVER", over_odds), ("UNDER", under_odds)):
                metrics = _nilai_ou_historis(gol_pairs, side, line, odds)
                if metrics is not None:
                    candidates.append({
                        "jenis": "OU",
                        "pick": f"{side} {float(line):g}",
                        "odds": round(float(odds), 2),
                        "prob": metrics["prob"],
                        "gap": metrics["gap"],
                        "push_rate": metrics["push_rate"],
                        "expected_profit": metrics["expected_profit"],
                        "line": float(line),
                    })
            if candidates:
                opsi.append(max(candidates, key=lambda item: item["gap"]))
    
    # Sort by gap tertinggi
    opsi.sort(key=lambda x: -x["gap"])
    
    return opsi


# ========== FASE 1.5: VALUE COMPARISON (2 OPSI) ==========
def bandingkan_opsi_2(gol_pairs, ou_lines, odds_home, odds_draw, odds_away,
                      home_win_rate=0, away_win_rate=0, draw_rate=0):
    """
    Bandingkan opsi, return 2 opsi terbaik:
    - top_1x2: 1 opsi terbaik dari 1X2 (atau None)
    - top_ou: 1 opsi terbaik dari O/U (atau None)
    - titik_buta: info probabilitas 2.5
    """
    if hasattr(gol_pairs, "tolist"):
        gol_pairs = gol_pairs.tolist()
    elif gol_pairs is None:
        gol_pairs = []
    if not gol_pairs:
        return None, None, None
    
    total_gols = [float(g[0]) + float(g[1]) for g in gol_pairs]
    n = len(total_gols)
    
    # ===== Hitung titik buta 2.5 =====
    over_25_count = sum(1 for g in total_gols if g > 2.5)
    over_25_rate = (over_25_count / n) * 100
    titik_buta = {
        "line": 2.5,
        "over_rate": round(over_25_rate, 1),
        "ada_di_market": False,  # cek nanti
    }
    
    # Cek apakah 2.5 ada di market
    if ou_lines:
        for ou in ou_lines:
            try:
                if abs(float(ou.get("line")) - 2.5) < 0.01:
                    titik_buta["ada_di_market"] = True
                    break
            except (TypeError, ValueError):
                continue

    opsi = bandingkan_opsi(
        gol_pairs, ou_lines, odds_home, odds_draw, odds_away,
        home_win_rate=home_win_rate,
        away_win_rate=away_win_rate,
        draw_rate=draw_rate,
    )
    opsi_1x2 = [item for item in opsi if item["jenis"] == "1X2"]
    opsi_ou = [item for item in opsi if item["jenis"] == "OU"]
    top_1x2 = max(opsi_1x2, key=lambda item: item["gap"]) if opsi_1x2 else None
    top_ou = max(opsi_ou, key=lambda item: item["gap"]) if opsi_ou else None

    return top_1x2, top_ou, titik_buta

def main():
    print("=" * 70)
    print("🎯 PARLAY BUILDER v3 — BEST PICK")
    print("=" * 70)

    with open("output/match_full.json", "r", encoding="utf-8") as f:
        matches = json.load(f)
    print(f"\n📥 {len(matches)} match dari web")

    print("\n📊 Load database H2H...")
    df = load_h2h()
    print(f"   ✅ {len(df):,} baris")

    print("\n🔍 Analisa H2H + cari BEST PICK...")
    hasil = []
    for m in matches:
        h2h = cari_h2h(df, m["home"], m["away"])
        stats = analisa(
            h2h, m["home"], m["away"],
            odds_home=m.get("odds_home", 0),
            odds_draw=m.get("odds_draw", 0),
            odds_away=m.get("odds_away", 0),
            ou_lines=m.get("ou_lines", []),
        )

        # ===== Pilih market dari harga yang benar-benar tersedia =====
        if stats is not None:
            if stats.get("pick_jenis") in {"1X2", "OU"}:
                market_options = [
                    option for option in (stats.get("top_1x2"), stats.get("top_ou"))
                    if option and option.get("gap", 0) >= 5
                ]
                best_market = max(
                    market_options, key=lambda option: option["gap"]
                ) if market_options else None

                if best_market:
                    # Jangan paksa line 2.5; bandingkan pick terbaik yang
                    # tersedia dengan odds riil pada market 1X2 dan O/U.
                    odds_real = best_market["odds"]
                    stats["pick"] = best_market["pick"]
                    stats["pick_jenis"] = best_market["jenis"]
                    stats["pick_odds"] = odds_real
                    stats["pick_conf"] = best_market["prob"]
                    stats["pick_push_rate"] = best_market.get("push_rate", 0)
                    stats["pick_implied"] = round(100 / odds_real, 1)
                    stats["value_gap"] = best_market["gap"]
                    stats["kategori_gap"] = (
                        "VALUE" if best_market["gap"] >= 10 else "FAIR"
                    )
                    stats["pick_alasan"] = (
                        f"{best_market['pick']}: peluang bersyarat "
                        f"{best_market['prob']}%, gap {best_market['gap']:+.1f}%"
                    )
                elif stats.get("pick_jenis") == "OU":
                    # Jangan terbitkan O/U dari odds asumsi 1.90.
                    stats = None

        if stats is None:
            continue

        stats.update(m)
        hasil.append(stats)

    print(f"   ✅ {len(hasil)} match punya BEST PICK")

    if not hasil:
        print("\n❌ Tidak ada. Coba turunkan MIN_H2H atau MIN_CONF_PICK.")
        return

    # Sorting
    by_conf = sorted(hasil, key=lambda x: (-x["pick_conf"], -x["skor"]))
    by_skor = sorted(hasil, key=lambda x: -x["skor"])

    # ===== TAMPILKAN SEMUA BEST PICK =====
    print(f"\n\n{'='*70}")
    print(f"🎯 BEST PICK PER MATCH")
    print(f"{'='*70}")

    # Hitung event count dulu
    event_count = hitung_event_tersedia(hasil)
    
    # ===== EVENT TERSEDIA =====
    event_count = hitung_event_tersedia(hasil)
    for i, m in enumerate(by_conf, 1):
        emoji = {
            "1X2": "🏠",
            "OU": "⚽",
            "BTTS": "🥅",
        }.get(m["pick_jenis"], "🎯")

        # ===== FORMAT RINGKAS =====
        # Baris 1: Nomor, Liga (pendek), Tier
        liga_pendek = m['liga'].split()[0][:15] if m['liga'] else "?"
        # ===== FORMAT RINGKAS =====
        liga_pendek = m["liga"].split()[0][:15] if m["liga"] else "?"
        print(f"\n#{i} [{liga_pendek}] {m['home'][:18]} vs {m['away'][:18]} — {m['tier']}")
        # Ambil pick dari top_ou kalau ada (override)
        pick_display = m.get("pick", "?")
        conf_display = m.get("pick_conf", 0)
        odds_display = m.get("pick_odds", 0)
        jenis_display = m.get("pick_jenis", "")
        
        # Kalau pick_jenis OU dan top_ou ada, pakai top_ou
        if jenis_display == "OU" and m.get("top_ou"):
            pick_display = m["top_ou"]["pick"]
            conf_display = m["top_ou"]["prob"]
            odds_display = m["top_ou"]["odds"]
        push_display = (
            f" | push {m.get('pick_push_rate', 0)}%"
            if jenis_display == "OU" else ""
        )
        
        print(f"    H2H:{m['h2h']} Skor:{m['skor']} Gol:{m['gol_total']} | {emoji} {pick_display} {conf_display}%{push_display} ({odds_display})")
        gol_pairs_m = m.get("gol_pairs", [])
        if gol_pairs_m:
            total_gols = [g[0] + g[1] for g in gol_pairs_m]
            ou_info = []
            for line_cek in [2.5, 3.0, 3.5, 4.0]:
                over_count = sum(1 for g in total_gols if g > line_cek)
                rate = (over_count / len(total_gols)) * 100
                ou_info.append(f"{line_cek}={rate:.0f}%")
            print(f"    📊 {' '.join(ou_info)}")
            # Rekomendasi line O/U terbaik
            if gol_pairs_m:
                _total = [g[0] + g[1] for g in gol_pairs_m]
                _lines = [2.5, 3.0, 3.5, 4.0]
                _best = None
                for _l in _lines:
                    _cnt = sum(1 for g in _total if g > _l)
                    _rate = (_cnt / len(_total)) * 100
                    if _rate >= 60:
                        _best = (_l, _rate)
                if _best:
                    # ===== PREDIKSI MENTAH =====
                    top_1x2_m = m.get("top_1x2")
                    top_ou_m = m.get("top_ou")
                    titik_m = m.get("titik_buta")

                    # Titik buta
                    if titik_m:
                        status_market = "ada di market" if titik_m.get("ada_di_market") else "TIDAK ADA di market"
                        over_rate = titik_m["over_rate"]
                        under_rate = 100 - over_rate

                        # ===== 5 ZONA =====
                        if over_rate >= 70:
                            label = f"OVER 2.5 = {over_rate:.0f}% 🔥 KUAT"
                            info = "Jelas over — aman"
                        elif over_rate >= 60:
                            label = f"OVER 2.5 = {over_rate:.0f}% ⚠️ MEPET"
                            info = "1 gol bisa ubah — cek line 2.75 / 3.0"
                        elif over_rate >= 40:
                            label = f"NETRAL = O{over_rate:.0f}% / U{under_rate:.0f}% 🟡"
                            info = "Tidak jelas — hindari 2.5"
                        elif over_rate >= 30:
                            label = f"UNDER 2.5 = {under_rate:.0f}% ⚠️ MEPET"
                            info = "1 gol bisa ubah — cek line 2.75 / 3.0"
                        else:
                            label = f"UNDER 2.5 = {under_rate:.0f}% 🔥 KUAT"
                            info = "Jelas under — aman"

                        print(f"    📌 TITIK BUTA: {label} ({status_market})")
                        print(f"       💡 {info}")
                    # UTAMA (1X2)
                    if top_1x2_m:
                        status_gap = "✅" if top_1x2_m["gap"] >= 10 else "⚠️" if top_1x2_m["gap"] >= 5 else "🟡" if top_1x2_m["gap"] >= 0 else "❌"
                        print(f"    🎯 UTAMA (1X2): {top_1x2_m['pick']} @ {top_1x2_m['odds']} | prob {top_1x2_m['prob']}% | gap {top_1x2_m['gap']:+}% {status_gap}")

                    # ALTERNATIF (O/U)
                    if top_ou_m:
                        status_gap = "✅" if top_ou_m["gap"] >= 10 else "⚠️" if top_ou_m["gap"] >= 5 else "🟡" if top_ou_m["gap"] >= 0 else "❌"
                        push_text = (
                            f" | push {top_ou_m.get('push_rate', 0)}%"
                            if "push_rate" in top_ou_m else ""
                        )
                        print(f"    ⚽ ALTERNATIF (O/U): {top_ou_m['pick']} @ {top_ou_m['odds']} | prob {top_ou_m['prob']}%{push_text} | gap {top_ou_m['gap']:+}% {status_gap}")

    # ===== GENERATE SLIP =====

    def bikin_slip(matches, n, nama, kategori_filter=None):
        # Filter berdasarkan jenis
        if kategori_filter:
            ms = [m for m in matches if m["pick_jenis"] == kategori_filter]
        else:
            ms = matches

        if len(ms) < n:
            print(f"\n⚠️ {nama}: butuh {n} match, cuma ada {len(ms)}")
            return None

        slip = ms[:n]
        total_odds = 1.0

        print(f"\n{'='*70}")
        print(f"🎯 {nama} ({n} MATCH)")
        print(f"{'='*70}")

        for i, m in enumerate(slip, 1):
            # Ambil odds sesuai pick
            if m["pick_jenis"] == "1X2":
                if m["pick"] == "HOME":
                    odds = m["odds_home"]
                else:
                    odds = m["odds_away"]
            elif m["pick_jenis"] == "OU":
                if "OVER" in m["pick"]:
                    odds = m.get("ou_over") or 1.90
                else:
                    odds = m.get("ou_under") or 1.90
            elif m["pick_jenis"] == "BTTS":
                odds = 1.85  # default BTTS
            else:
                odds = 1.85

            total_odds *= odds

            print(f"\n{i}. [{m['liga']}] {m['home']} vs {m['away']}")
            print(f"   H2H: {m['h2h']}x | Skor: {m['skor']} | {m['tier']}")
            print(f"   🎯 {m['pick']} ({m['pick_conf']}%) | odds {odds:.2f}")
            # Alasan sesuai pick (dari market)
            pick_now = m.get("pick", "")
            if pick_now.startswith("OVER") or pick_now.startswith("UNDER"):
                top_ou_a = m.get("top_ou")
                if top_ou_a:
                    print(f"   └─ {top_ou_a['pick']}: prob bersyarat {top_ou_a['prob']}% | push {top_ou_a.get('push_rate', 0)}% | gap {top_ou_a['gap']:+}%")
                else:
                    print(f"   └─ {m['pick_alasan']}")
            else:
                print(f"   └─ {m['pick_alasan']}")

        potensi = MODAL * total_odds
        print(f"\n💰 Odds Gabungan: {total_odds:.2f}")
        print(f"💰 Modal: Rp {MODAL:,}")
        print(f"💰 Potensi Return: Rp {potensi:,.0f}")
        print(f"💰 Potensi Profit: Rp {potensi - MODAL:,.0f}")

        return {
            "nama": nama,
            "n": n,
            "total_odds": round(total_odds, 2),
            "potensi": potensi,
        }

    print(f"\n\n{'#'*70}")
    print(f"# GENERATE SLIP")
    print(f"{'#'*70}")

    # ===== KATEGORI SLIP BARU =====
    
    # Debug: tampilkan semua value_gap
    print(f"\n📊 Detail semua {len(by_conf)} match:")
    for m in by_conf:
        print(f"   {m['home']:25} vs {m['away']:25} | "
              f"pick={m['pick']:12} | conf={m['pick_conf']:5}% | "
              f"odds={m.get('pick_odds', 0):.2f} | gap={m.get('value_gap', 0):+.1f}% | "
              f"kat={m.get('kategori_gap', '-')}")
    
    # ===== PISAHKAN PER TIER =====
    # Tier: T1 (skor >= 400), T2 (250-399), T3 (<250)
    t1 = [m for m in hasil if "T1" in m.get("tier", "")]
    t2 = [m for m in hasil if "T2" in m.get("tier", "")]
    t3 = [m for m in hasil if "T3" in m.get("tier", "")]
    
    print(f"\n📊 DISTRIBUSI TIER:")
    print(f"   🔥 TIER 1 (skor >= 400): {len(t1)} match")
    print(f"   ⚡ TIER 2 (skor 250-399): {len(t2)} match")
    print(f"   ✅ TIER 3 (skor < 250): {len(t3)} match")
    
    # Tampilkan detail per tier
    for nama_tier, tim_list in [("🔥 TIER 1", t1), ("⚡ TIER 2", t2), ("✅ TIER 3", t3)]:
        if not tim_list:
            continue
        print(f"\n{nama_tier}:")
        for i, m in enumerate(tim_list, 1):
            jenis = m.get("pick_jenis", "")
            emoji = {"1X2": "🏠", "OU": "⚽", "BTTS": "🥅"}.get(jenis, "🎯")
            print(f"   {i}. {m['home'][:20]:20} vs {m['away'][:20]:20}")
            print(f"      {emoji} {m['pick']:15} ({m['pick_conf']}%) | odds {m.get('pick_odds', 0)} | skor {m['skor']}")
    
    # ===== GENERATE SLIP PER TIER =====
    print(f"\n{'#'*60}")
    print(f"# GENERATE SLIP PER TIER")
    print(f"{'#'*60}")
    
    def bikin_slip_tier(tim_list, nama, n_min=2, n_max=5):
        """Bikin slip dari 1 tier saja"""
        if len(tim_list) < n_min:
            print(f"\n⚠️ {nama}: tidak cukup match (butuh min {n_min}, ada {len(tim_list)})")
            return None
        
        n = min(n_max, len(tim_list))
        slip = sorted(tim_list, key=lambda x: -x.get("pick_conf", 0))[:n]
        
        total_odds = 1.0
        for p in slip:
            total_odds *= p.get("pick_odds", 1)
        
        print(f"\n{'='*60}")
        print(f"🎯 {nama} ({n} MATCH)")
        print(f"{'='*60}")
        
        for i, m in enumerate(slip, 1):
            jenis = m.get("pick_jenis", "")
            emoji = {"1X2": "🏠", "OU": "⚽", "BTTS": "🥅"}.get(jenis, "🎯")
            print(f"\n{i}. [{m['liga']}]")
            print(f"   {m['home']} vs {m['away']} ({m['waktu']})")
            print(f"   H2H: {m['h2h']}x | Skor: {m['skor']} | {m['tier']}")
            print(f"   {emoji} {m['pick']} ({m['pick_conf']}%) | odds {m.get('pick_odds', 0)}")
            # Alasan sesuai pick (dari market)
            pick_now = m.get("pick", "")
            if pick_now.startswith("OVER") or pick_now.startswith("UNDER"):
                top_ou_a = m.get("top_ou")
                if top_ou_a:
                    print(f"   └─ {top_ou_a['pick']}: prob bersyarat {top_ou_a['prob']}% | push {top_ou_a.get('push_rate', 0)}% | gap {top_ou_a['gap']:+}%")
                else:
                    print(f"   └─ {m['pick_alasan']}")
            else:
                print(f"   └─ {m['pick_alasan']}")
            
            # Info non-loss untuk 1X2
            if m.get("pick_jenis") == "1X2":
                non_loss = m.get("non_loss_rate", 0)
                if non_loss > 0:
                    print(f"   📊 Non-Loss: {non_loss}%")
        
        potensi = 100_000 * total_odds
        print(f"\n💰 Total Odds: {total_odds:.2f}")
        print(f"💰 Modal: Rp 100,000")
        print(f"💰 Potensi: Rp {potensi:,.0f}")
        
        return slip
    
    # Generate per tier
    bikin_slip_tier(t1, "🥇 SLIP TIER 1 (SKOR TERTINGGI)")
    bikin_slip_tier(t2, "🥈 SLIP TIER 2 (SKOR SEDANG)")
    bikin_slip_tier(t3, "🥉 SLIP TIER 3 (SKOR RENDAH)")
    
    # Combined hanya kalau T1 cuma 1 match
    if len(t1) == 1 and len(t2) + len(t3) > 0:
        print(f"\n{'='*60}")
        print(f"⚠️ T1 cuma 1 match — kombinasi dengan T2")
        print(f"{'='*60}")
        t1_t2 = t1 + t2
        if len(t1_t2) >= 2:
            bikin_slip_tier(t1_t2, "🥇 SLIP T1 + T2", n_min=2, n_max=4)
    
# Simpan
    def convert(obj):
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(x) for x in obj]
        elif hasattr(obj, "item"):
            return obj.item()
        return obj

    with open("output/best_pick.json", "w", encoding="utf-8") as f:
        json.dump(convert(hasil), f, indent=2, ensure_ascii=False)
    print(f"\n💾 Disimpan: output/best_pick.json")


if __name__ == "__main__":
    main()
