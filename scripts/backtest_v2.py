"""
BACKTEST v2 — Versi Benar
- Hindari data leakage (H2H hanya dari masa lalu)
- Sample besar
- Output lengkap
"""
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import os
import sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# ========== KONFIGURASI ==========
MIN_H2H = 5
MIN_HOME = 5
MIN_AWAY = 5
MIN_CONF = 65
MIN_ODDS = 1.30
MAX_ODDS = 4.00

# Batas waktu: H2H hanya dari N hari sebelum match
H2H_WINDOW_DAYS = 365 * 3  # 3 tahun terakhir

# Sample size
SAMPLE_SIZE = 5000


def load_h2h():
    """Load semua database H2H dengan tanggal"""
    data = []
    
    # Top leagues
    try:
        df = pd.read_csv("data/football_data/all_football_data.csv", low_memory=False)
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG", "Date"])
        df = df[["HomeTeam", "AwayTeam", "FTHG", "FTAG", "League", "Season", "Date"]].copy()
        df.columns = ["home", "away", "hg", "ag", "league", "season", "date"]
        data.append(df)
    except Exception as e:
        print(f"⚠️ Top: {e}")
    
    # Extra leagues
    try:
        df = pd.read_csv("data/football_data_extra/all_extra.csv", low_memory=False)
        df = df.dropna(subset=["Home", "Away", "HG", "AG", "Date"])
        liga_col = "LeagueName" if "LeagueName" in df.columns else "League"
        df = df[["Home", "Away", "HG", "AG", liga_col, "Season", "Date"]].copy()
        df.columns = ["home", "away", "hg", "ag", "league", "season", "date"]
        data.append(df)
    except Exception as e:
        print(f"⚠️ Extra: {e}")
    
    df = pd.concat(data, ignore_index=True)
    df["hg"] = pd.to_numeric(df["hg"], errors="coerce")
    df["ag"] = pd.to_numeric(df["ag"], errors="coerce")
    df = df.dropna(subset=["hg", "ag"])
    
    # Parse tanggal
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    
    return df


def backtest_v2(df):
    """Backtest dengan hindari data leakage"""
    
    print(f"📊 Total data: {len(df):,} match")
    print(f"📅 Range: {df['date'].min()} s/d {df['date'].max()}")
    
    # Ambil sample dari match terakhir
    if len(df) > SAMPLE_SIZE:
        df_test = df.tail(SAMPLE_SIZE).copy()
        df_hist = df  # pakai semua data untuk H2H
    else:
        df_test = df.copy()
        df_hist = df
    
    print(f"\n🎯 Test {len(df_test)} match terakhir...\n")
    
    hasil = {
        "total": 0,
        "menang": 0,
        "kalah": 0,
        "skip": 0,
        "profit_total": 0,
        "modal_total": 0,
        "detail": [],
        "per_liga": defaultdict(lambda: {"total": 0, "menang": 0}),
        "per_conf": defaultdict(lambda: {"total": 0, "menang": 0}),
    }
    
    # Cache H2H untuk performa
    h2h_cache = {}
    
    for idx, row in df_test.iterrows():
        home = row["home"]
        away = row["away"]
        hg = row["hg"]
        ag = row["ag"]
        liga = row["league"]
        tanggal = row["date"]
        
        # Key cache
        cache_key = (home, away, tanggal)
        if cache_key in h2h_cache:
            h2h = h2h_cache[cache_key]
        else:
            # H2H dari masa lalu (sebelum tanggal match)
            cutoff_date = tanggal - pd.Timedelta(days=H2H_WINDOW_DAYS)
            
            mask = (
                ((df_hist["home"] == home) & (df_hist["away"] == away)) |
                ((df_hist["home"] == away) & (df_hist["away"] == home))
            )
            h2h = df_hist[mask & (df_hist["date"] < tanggal)].copy()
            h2h_cache[cache_key] = h2h
        
        if len(h2h) < MIN_H2H:
            hasil["skip"] += 1
            continue
        
        # Hitung win rate
        def is_home(r):
            return r["home"] == home
        
        h2h = h2h.copy()
        h2h["home_is_A"] = h2h.apply(is_home, axis=1)
        
        def result(r):
            if r["home_is_A"]:
                h, a = r["hg"], r["ag"]
            else:
                h, a = r["ag"], r["hg"]
            if h > a: return "W"
            elif h < a: return "L"
            return "D"
        
        h2h["result"] = h2h.apply(result, axis=1)
        menang_a = (h2h["result"] == "W").sum()
        win_rate = (menang_a / len(h2h)) * 100
        
        # Rekomendasi 1X2
        if win_rate >= 60:
            pick = "HOME"
            conf = min(95, 50 + (win_rate - 50) * 1.5)
        elif win_rate <= 30:
            pick = "AWAY"
            conf = min(95, 50 + (30 - win_rate) * 1.5)
        else:
            hasil["skip"] += 1
            continue
        
        if conf < MIN_CONF:
            hasil["skip"] += 1
            continue
        
        # Cek hasil aktual
        if pick == "HOME":
            menang_aktual = hg > ag
        else:
            menang_aktual = ag > hg
        
        # Asumsi odds (bisa diganti dengan odds real)
        # Pakai odds estimated berdasarkan confidence
        # Kalau confidence tinggi, odds rendah
        estimated_odds = max(MIN_ODDS, min(MAX_ODDS, 100 / (conf + 5)))
        
        hasil["total"] += 1
        hasil["modal_total"] += 100_000
        
        if menang_aktual:
            hasil["menang"] += 1
            profit = 100_000 * (estimated_odds - 1)
            hasil["profit_total"] += profit
        else:
            hasil["kalah"] += 1
            hasil["profit_total"] -= 100_000
        
        # Per liga
        hasil["per_liga"][liga]["total"] += 1
        if menang_aktual:
            hasil["per_liga"][liga]["menang"] += 1
        
        # Per confidence range
        conf_range = f"{(conf // 10) * 10}-{(conf // 10) * 10 + 9}%"
        hasil["per_conf"][conf_range]["total"] += 1
        if menang_aktual:
            hasil["per_conf"][conf_range]["menang"] += 1
        
        hasil["detail"].append({
            "tanggal": str(tanggal.date()),
            "liga": liga,
            "home": home,
            "away": away,
            "pick": pick,
            "conf": round(conf, 1),
            "win_rate": round(win_rate, 1),
            "estimated_odds": round(estimated_odds, 2),
            "hg": hg,
            "ag": ag,
            "menang": menang_aktual,
            "profit": round(profit if menang_aktual else -100_000),
        })
    
    return hasil


def main():
    print("=" * 60)
    print("🔬 BACKTEST v2 — Test Valid (No Data Leakage)")
    print("=" * 60)
    
    df = load_h2h()
    if len(df) == 0:
        print("❌ Tidak ada data")
        return
    
    print(f"\n⏳ Loading... \n")
    hasil = backtest_v2(df)
    
    print("=" * 60)
    print("📊 HASIL BACKTEST v2")
    print("=" * 60)
    
    total = hasil["total"]
    menang = hasil["menang"]
    kalah = hasil["kalah"]
    skip = hasil["skip"]
    
    if total == 0:
        print("❌ Tidak ada match yang lolos filter")
        return
    
    print(f"\n📈 SAMPLE:")
    print(f"  Total dites:        {total + skip}")
    print(f"  Lolos filter:       {total}")
    print(f"  Skip (H2H tipis):   {skip}")
    
    print(f"\n📊 HASIL:")
    print(f"  ✅ Menang:          {menang} ({menang/total*100:.1f}%)")
    print(f"  ❌ Kalah:           {kalah} ({kalah/total*100:.1f}%)")
    
    print(f"\n💰 KEUANGAN:")
    print(f"  Modal total:        Rp {hasil['modal_total']:,}")
    print(f"  Profit:             Rp {hasil['profit_total']:+,.0f}")
    roi = (hasil['profit_total'] / hasil['modal_total']) * 100
    print(f"  ROI:                {roi:+.1f}%")
    
    # Per liga
    print(f"\n📊 PER LIGA (top 10):")
    liga_sorted = sorted(hasil["per_liga"].items(),
                         key=lambda x: x[1]["total"], reverse=True)[:10]
    for liga, stats in liga_sorted:
        if stats["total"] >= 5:
            wr = stats["menang"] / stats["total"] * 100
            print(f"  {liga[:35]:35} {stats['total']:4} match | {wr:5.1f}%")
    
    # Per confidence
    print(f"\n📊 PER CONFIDENCE:")
    for conf_r, stats in sorted(hasil["per_conf"].items()):
        if stats["total"] >= 5:
            wr = stats["menang"] / stats["total"] * 100
            print(f"  {conf_r:15} {stats['total']:4} match | {wr:5.1f}%")
    
    # Simpan detail
    if hasil["detail"]:
        df_detail = pd.DataFrame(hasil["detail"])
        df_detail.to_csv("output/backtest_v2_result.csv", index=False)
        print(f"\n💾 Detail: output/backtest_v2_result.csv")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
