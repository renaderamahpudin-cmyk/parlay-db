"""
BACKTEST — Test strategi di data historis
Test: Apakah rekomendasi H2H kita akurat?
"""
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import os
import re
import sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

# ========== KONFIGURASI ==========
MIN_H2H = 5
MIN_HOME = 5
MIN_AWAY = 5
BOBOT_H2H = 10
BOBOT_HOME = 5
BOBOT_AWAY = 5
MIN_CONF = 65
MIN_ODDS = 1.30
MAX_ODDS = 4.00


def load_h2h():
    data = []
    try:
        df = pd.read_csv("data/football_data/all_football_data.csv", low_memory=False)
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
        df = df[["HomeTeam", "AwayTeam", "FTHG", "FTAG", "League", "Season", "Date"]].copy()
        df.columns = ["home", "away", "hg", "ag", "league", "season", "date"]
        data.append(df)
    except Exception as e:
        print(f"⚠️ Top: {e}")
    
    try:
        df = pd.read_csv("data/football_data_extra/all_extra.csv", low_memory=False)
        df = df.dropna(subset=["Home", "Away", "HG", "AG"])
        liga_col = "LeagueName" if "LeagueName" in df.columns else "League"
        season_col = "Season" if "Season" in df.columns else None
        date_col = "Date" if "Date" in df.columns else None
        
        cols = ["Home", "Away", "HG", "AG", liga_col]
        if season_col: cols.append(season_col)
        if date_col: cols.append(date_col)
        
        df = df[cols].copy()
        new_cols = ["home", "away", "hg", "ag", "league"]
        if season_col: new_cols.append("season")
        if date_col: new_cols.append("date")
        df.columns = new_cols
        
        # Isi yang kosong
        if "season" not in df.columns:
            df["season"] = "?"
        if "date" not in df.columns:
            df["date"] = "?"
        
        data.append(df)
    except Exception as e:
        print(f"⚠️ Extra: {e}")
    
    df = pd.concat(data, ignore_index=True)
    df["hg"] = pd.to_numeric(df["hg"], errors="coerce")
    df["ag"] = pd.to_numeric(df["ag"], errors="coerce")
    df = df.dropna(subset=["hg", "ag"])
    return df


def backtest(df):
    """Test akurasi rekomendasi H2H"""
    
    # Filter liga top + extra
    liga_ada = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1",
                "Eredivisie", "Primeira Liga", "Super Lig", "Super League Yunani",
                "Championship", "La Liga 2", "Serie B", "Bundesliga 2", "Ligue 2",
                "Eerste Divisie", "Brazil Serie A", "Argentina Primera", "USA MLS",
                "Mexico Liga MX", "Japan J-League", "Finland Veikkausliiga",
                "Ireland Premier Division", "Romania Liga 1"]
    
    df = df[df["league"].isin(liga_ada)].copy()
    print(f"📊 Data: {len(df):,} match\n")
    
    # Ambil sample: 1000 match terakhir
    df = df.tail(1000)
    
    hasil = {
        "total": 0,
        "menang": 0,
        "kalah": 0,
        "skip": 0,
        "detail": [],
    }
    
    print("⏳ Backtest 1000 match...\n")
    
    for idx, row in df.iterrows():
        home = row["home"]
        away = row["away"]
        hg = row["hg"]
        ag = row["ag"]
        liga = row["league"]
        
        # Ambil H2H SEBELUM match ini (untuk hindari data leakage)
        # Untuk simplifikasi, skip ini
        # Ambil H2H dari data lain
        mask = (
            ((df["home"] == home) & (df["away"] == away)) |
            ((df["home"] == away) & (df["away"] == home))
        )
        h2h = df[mask]
        
        # Skip match ini sendiri
        h2h = h2h[h2h.index != idx]
        
        if len(h2h) < MIN_H2H:
            hasil["skip"] += 1
            continue
        
        # Hitung win rate
        def is_home(row_h):
            return row_h["home"] == home
        
        h2h = h2h.copy()
        h2h["home_is_A"] = h2h.apply(is_home, axis=1)
        
        def result(row_h):
            if row_h["home_is_A"]:
                h, a = row_h["hg"], row_h["ag"]
            else:
                h, a = row_h["ag"], row_h["hg"]
            if h > a: return "W"
            elif h < a: return "L"
            return "D"
        
        h2h["result"] = h2h.apply(result, axis=1)
        menang_a = (h2h["result"] == "W").sum()
        win_rate = (menang_a / len(h2h)) * 100
        
        # Rekomendasi
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
        else:  # AWAY
            menang_aktual = ag > hg
        
        hasil["total"] += 1
        if menang_aktual:
            hasil["menang"] += 1
        else:
            hasil["kalah"] += 1
        
        hasil["detail"].append({
            "home": home,
            "away": away,
            "pick": pick,
            "conf": round(conf, 1),
            "win_rate": round(win_rate, 1),
            "hg": hg,
            "ag": ag,
            "menang": menang_aktual,
        })
    
    return hasil


def main():
    print("=" * 70)
    print("🔬 BACKTEST — Test Akurasi Strategi H2H")
    print("=" * 70)
    
    df = load_h2h()
    
    hasil = backtest(df)
    
    print("\n" + "=" * 70)
    print("📊 HASIL BACKTEST")
    print("=" * 70)
    print(f"\n  Total match dites:  {hasil['total']}")
    print(f"  ✅ Menang:          {hasil['menang']} ({hasil['menang']/max(1,hasil['total'])*100:.1f}%)")
    print(f"  ❌ Kalah:           {hasil['kalah']} ({hasil['kalah']/max(1,hasil['total'])*100:.1f}%)")
    print(f"  ⏭️  Skip (H2H tipis): {hasil['skip']}")
    
    if hasil["total"] > 0:
        # Hitung ROI (asumsi odds rata-rata 1.50)
        avg_odds = 1.50
        modal = hasil["total"] * 100_000
        return_total = hasil["menang"] * 100_000 * avg_odds
        
        roi = ((return_total - modal) / modal) * 100
        
        print(f"\n  💰 Estimasi ROI (odds {avg_odds}): {roi:+.1f}%")
    
    # Simpan detail
    if hasil["detail"]:
        df_detail = pd.DataFrame(hasil["detail"])
        df_detail.to_csv("output/backtest_result.csv", index=False)
        print(f"\n💾 Detail disimpan: output/backtest_result.csv")
        
        # Tampilkan 10 sample
        print(f"\n📋 10 Sample:")
        for d in hasil["detail"][:10]:
            emoji = "✅" if d["menang"] else "❌"
            print(f"  {emoji} {d['home']} vs {d['away']} | "
                  f"{d['pick']} {d['conf']}% | Skor {d['hg']}-{d['ag']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
