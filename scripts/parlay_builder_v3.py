"""Parlay builder focused on market-priced Over/Under recommendations."""
import warnings
warnings.filterwarnings("ignore")
import json
import math
import pandas as pd
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pick_policy import (
    MAX_OU_GAP, MAX_OU_ODDS, MIN_OU_GAP, MIN_OU_ODDS, is_eligible_ou_pick,
)
from settlement import settle_pick
from backtest_ou_walkforward import load_matches
from ou_model import (
    TEAM_ALIASES,
    WalkForwardModel,
    compare_market_line,
    normalize_team,
)
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
ALIAS = TEAM_ALIASES


def normalize(name):
    return normalize_team(name)


def load_h2h():
    """Load dated match results and shot data used by the point-in-time model."""
    return load_matches()


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


def analisa_ou(
    h2h,
    home_web,
    ou_lines=None,
    *,
    away_web=None,
    model=None,
    as_of=None,
    league="?",
):
    """Build an O/U recommendation from recent venue form and Poisson pricing."""
    if not ou_lines or model is None or not away_web or as_of is None:
        return None
    prediction = model.predict(
        home_web, away_web, as_of, league=league
    )
    if not prediction.get("available"):
        return None

    candidates = []
    all_lines = []
    for market_line in ou_lines:
        try:
            line = float(market_line.get("line"))
            odds_over = float(market_line.get("over"))
            odds_under = float(market_line.get("under"))
            if (
                not math.isfinite(line)
                or not math.isfinite(odds_over)
                or not math.isfinite(odds_under)
                or odds_over <= 1
                or odds_under <= 1
            ):
                continue
            comparison = compare_market_line(
                prediction["lambda_home"],
                prediction["lambda_away"],
                line,
                odds_over,
                odds_under,
            )
        except (TypeError, ValueError):
            continue
        all_lines.append(comparison)
        for side in ("over", "under"):
            metrics = comparison[side]
            odds = metrics["odds"]
            gap = metrics["value_gap"]
            expected_return = metrics["expected_return"]
            if gap is None or not MIN_OU_ODDS <= odds <= MAX_OU_ODDS:
                continue
            option = {
                "jenis": "OU",
                "pick": f"{side.upper()} {line:g}",
                "odds": round(odds, 2),
                "prob": round(metrics["conditional_probability"] * 100, 2),
                "gap": round(gap, 2),
                "market_no_vig": round(
                    metrics["market_no_vig_probability"] * 100, 2
                ),
                "overround": round(
                    comparison["market_overround_pct"], 2
                ),
                "expected_profit": round(expected_return, 5),
                "line": line,
                "settlement_probabilities": {
                    "full_win": round(metrics["full_win"] * 100, 2),
                    "half_win": round(metrics["half_win"] * 100, 2),
                    "push": round(metrics["push"] * 100, 2),
                    "half_loss": round(metrics["half_loss"] * 100, 2),
                    "full_loss": round(metrics["full_loss"] * 100, 2),
                },
            }
            eligibility_record = {
                "pick_jenis": "OU",
                "pick": option["pick"],
                "pick_odds": option["odds"],
                "pick_conf": option["prob"],
                "value_gap": option["gap"],
            }
            if (
                MIN_OU_GAP <= option["gap"] <= MAX_OU_GAP
                and expected_return > 0
                and is_eligible_ou_pick(eligibility_record)
            ):
                candidates.append(option)

    if not candidates:
        return None
    # Expected return is the primary ranking; gap is a secondary tie-breaker.
    best = max(
        candidates,
        key=lambda option: (option["expected_profit"], option["gap"]),
    )
    form_score = round(
        100 * min(prediction["home_form_count"], prediction["away_form_count"])
        / 10
    )
    tier = "🔥 T1" if form_score >= 90 else "⚡ T2" if form_score >= 70 else "✅ T3"
    h2h_count = prediction["h2h_before"]
    best_25 = next(
        (item for item in all_lines if math.isclose(item["line"], 2.5)),
        None,
    )

    return {
        "h2h": h2h_count,
        "gol_pairs": [],
        "gol_total": round(prediction["expected_total"], 2),
        "lambda_home": round(prediction["lambda_home"], 3),
        "lambda_away": round(prediction["lambda_away"], 3),
        "home_form_n": prediction["home_form_count"],
        "away_form_n": prediction["away_form_count"],
        "baseline_source": prediction["baseline_source"],
        "uses_shot_proxy": prediction["uses_shot_proxy"],
        "skor": form_score,
        "tier": tier,
        "pick_jenis": "OU",
        "pick": best["pick"],
        "pick_conf": best["prob"],
        "pick_push_rate": best["settlement_probabilities"]["push"],
        "pick_odds": best["odds"],
        "pick_implied": best["market_no_vig"],
        "value_gap": best["gap"],
        "pick_expected_return": best["expected_profit"],
        "kategori_gap": "VALUE" if best["gap"] >= 10 else "FAIR",
        "pick_alasan": (
            f"{best['pick']}: peluang settlement efektif {best['prob']}%, "
            f"gap no-vig {best['gap']:+.2f} pp, "
            f"EV {best['expected_profit']:+.3f} unit"
        ),
        "top_ou": best,
        "titik_buta": {
            "line": 2.5,
            "over_rate": (
                round(best_25["over"]["conditional_probability"] * 100, 2)
                if best_25 else None
            ),
            "ada_di_market": best_25 is not None,
        },
    }


def main():
    print("=" * 70)
    print("⚽ PARLAY BUILDER v3 — O/U ONLY")
    print("=" * 70)

    with open("output/match_full.json", "r", encoding="utf-8") as f:
        matches = json.load(f)
    print(f"\n📥 {len(matches)} match dari web")

    print("\n📊 Load database pertandingan, gol, dan tembakan...")
    df = load_h2h()
    print(f"   ✅ {len(df):,} baris")

    as_of = pd.Timestamp.now().normalize()
    model = WalkForwardModel()
    prior_matches = df.loc[df["date"] < as_of]
    print(
        f"   🔒 Muat {len(prior_matches):,} laga sebelum "
        f"{as_of.date().isoformat()} (tanggal yang sama tidak dipakai)"
    )
    print(
        "   ⚠️ Model masih eksperimental; EV adalah estimasi dan "
        "gap +5 pp belum terbukti menghasilkan ROI positif."
    )
    for row in prior_matches.to_dict(orient="records"):
        model.update(row)

    print("\n🔍 Analisa form kandang/tandang + Poisson + expected return...")
    hasil = []
    for m in matches:
        stats = analisa_ou(
            None,
            m["home"],
            ou_lines=m.get("ou_lines", []),
            away_web=m["away"],
            model=model,
            as_of=as_of,
            league=m.get("liga", "?"),
        )
        if stats is None or not is_eligible_ou_pick(stats):
            continue

        hasil.append({**m, **stats})

    print(f"   ✅ {len(hasil)} match punya BEST PICK")
    print(f"   ⏭️  Skip/tidak layak O/U: {len(matches) - len(hasil)}")

    if not hasil:
        print(
            f"\n❌ Tidak ada pick O/U yang memenuhi gap minimum "
            f"+{MIN_OU_GAP:.0f}% dan odds pasar yang valid."
        )

    # Sorting
    by_conf = sorted(
        hasil,
        key=lambda x: (
            -x["pick_expected_return"], -x["value_gap"], -x["pick_conf"]
        ),
    )
    by_skor = sorted(hasil, key=lambda x: -x["skor"])

    # ===== TAMPILKAN PICK O/U YANG LOLOS FILTER =====
    print(f"\n\n{'='*70}")
    print(f"⚽ REKOMENDASI O/U — GAP MINIMUM +{MIN_OU_GAP:.0f}%")
    print(f"{'='*70}")

    for i, m in enumerate(by_conf, 1):
        print(
            f"\n#{i} [{m.get('liga', '?')}] "
            f"{m.get('home', '?')} vs {m.get('away', '?')} — {m['tier']}"
        )
        print(
            f"   ⚽ {m['pick']} | peluang settlement efektif {m['pick_conf']}% "
            f"| push {m['pick_push_rate']}% | odds {m['pick_odds']:.2f}"
        )
        print(
            f"   Gap no-vig {m['value_gap']:+.2f} pp | "
            f"EV {m['pick_expected_return']:+.3f} unit "
            f"| λ gol {m['lambda_home']:.2f}-{m['lambda_away']:.2f}"
        )
        print(
            f"   Form kandang/tandang {m['home_form_n']}/{m['away_form_n']} "
            f"| H2H {m['h2h']} (bobot 10%) | {m['kategori_gap']}"
        )

    # ===== GENERATE SLIP =====
    print(f"\n\n{'#'*70}")
    print(f"# GENERATE SLIP O/U — GAP MINIMUM +{MIN_OU_GAP:.0f}%")
    print(f"{'#'*70}")

    # ===== KATEGORI SLIP BARU =====
    
    # Debug: tampilkan semua value_gap
    print(f"\n📊 Detail semua {len(by_conf)} match:")
    for m in by_conf:
        print(f"   {m['home']:25} vs {m['away']:25} | "
              f"O/U={m['pick']:12} | peluang={m['pick_conf']:5}% | "
              f"odds={m['pick_odds']:.2f} | EV={m['pick_expected_return']:+.3f}")
    
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
            print(f"   {i}. {m['home'][:20]:20} vs {m['away'][:20]:20}")
            print(
                f"      ⚽ {m['pick']:15} ({m['pick_conf']}%) "
                f"| EV {m['pick_expected_return']:+.3f} "
                f"| odds {m['pick_odds']:.2f}"
            )
    
    # ===== GENERATE SLIP PER TIER =====
    print(f"\n{'#'*60}")
    print(f"# GENERATE SLIP PER TIER")
    print(f"{'#'*60}")
    
    def bikin_slip_tier(tim_list, nama, n_min=2, n_max=5):
        """Build a slip only from approved O/U picks."""
        eligible = [pick for pick in tim_list if is_eligible_ou_pick(pick)]
        if len(eligible) < n_min:
            print(
                f"\n⚠️ {nama}: tidak cukup pick O/U dengan gap "
                f">=+{MIN_OU_GAP:.0f}% (butuh {n_min}, ada {len(eligible)})"
            )
            return None
        
        n = min(n_max, len(eligible))
        slip = sorted(
            eligible,
            key=lambda x: (
                -x["pick_expected_return"], -x["value_gap"], -x["pick_conf"]
            ),
        )[:n]
        
        total_odds = 1.0
        for p in slip:
            total_odds *= p["pick_odds"]
        
        print(f"\n{'='*60}")
        print(f"🎯 {nama} ({n} MATCH)")
        print(f"{'='*60}")
        
        for i, m in enumerate(slip, 1):
            print(f"\n{i}. [{m['liga']}]")
            print(f"   {m['home']} vs {m['away']} ({m['waktu']})")
            print(f"   H2H: {m['h2h']}x | Skor: {m['skor']} | {m['tier']}")
            print(
                f"   ⚽ {m['pick']} | peluang settlement efektif {m['pick_conf']}% "
                f"| push {m['pick_push_rate']}% | odds {m['pick_odds']:.2f}"
            )
            print(
                f"   Gap no-vig {m['value_gap']:+.2f} pp "
                f"| EV {m['pick_expected_return']:+.3f} unit "
                f"| {m['kategori_gap']}"
            )
        
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
