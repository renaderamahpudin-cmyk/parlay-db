"""
TRACK RECORD — Catat Hasil Prediksi vs Aktual
"""
import json
import os
import pandas as pd
from datetime import datetime

from pick_policy import is_eligible_ou_pick
from settlement import TRACK_COLUMNS, match_key, settle_pick

TRACK_FILE = "output/track_record.csv"


def load_track():
    if os.path.exists(TRACK_FILE):
        df = pd.read_csv(TRACK_FILE)
    else:
        df = pd.DataFrame(columns=TRACK_COLUMNS)
    for column in TRACK_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    return df


def init_track():
    """Bikin file track kalau belum ada"""
    if os.path.exists(TRACK_FILE):
        df = load_track()
        df.to_csv(TRACK_FILE, index=False)
        return
    df = pd.DataFrame(columns=TRACK_COLUMNS)
    df.to_csv(TRACK_FILE, index=False)
    print(f"✅ File baru: {TRACK_FILE}")


def add_match_manual():
    """Input manual hasil match"""
    print("\n" + "=" * 60)
    print("INPUT HASIL MATCH")
    print("=" * 60)
    
    # Load best_pick and omit fixtures already recorded automatically or manually.
    with open("output/best_pick.json") as f:
        picks = json.load(f)
    df = load_track()
    tracked = {
        match_key(row.liga, row.home, row.away)
        for row in df[["liga", "home", "away"]].itertuples(index=False)
        if pd.notna(row.home) and pd.notna(row.away)
    }
    picks = [
        p for p in picks
        if is_eligible_ou_pick(p)
        and match_key(p.get("liga"), p.get("home"), p.get("away")) not in tracked
    ]
    
    print(f"\nTotal pick tersedia: {len(picks)}")
    if not picks:
        print("📭 Tidak ada pick baru yang belum ditrack.")
        return
    print("\nPilih match (nomor):")
    for i, p in enumerate(picks, 1):
        print(f"  [{i}] {p['home']} vs {p['away']} — {p['pick']}")
    
    try:
        idx = int(input("\nNomor match: ")) - 1
        if idx < 0 or idx >= len(picks):
            print("❌ Nomor tidak valid")
            return
        
        p = picks[idx]
        
        # Input skor
        skor_home = int(input(f"Skor {p['home']}: "))
        skor_away = int(input(f"Skor {p['away']}: "))
        if skor_home < 0 or skor_away < 0:
            print("❌ Skor tidak boleh negatif")
            return
        total_gol = skor_home + skor_away
        
        # Tentukan hasil
        pick = p.get("pick", "")
        conf = p.get("pick_conf", 0)
        odds = p.get("pick_odds") or p.get("odds")
        hasil, profit = settle_pick(pick, skor_home, skor_away, odds)
        
        # Simpan
        row = {
            "tanggal": datetime.now().strftime("%Y-%m-%d"),
            "liga": p.get("liga", "?"),
            "home": p["home"],
            "away": p["away"],
            "pick": pick,
            "conf": conf,
            "odds": odds,
            "skor": p.get("skor", 0),
            "tier": p.get("tier", "?"),
            "pick_push_rate": p.get("pick_push_rate", 0),
            "skor_home": skor_home,
            "skor_away": skor_away,
            "total_gol": total_gol,
            "hasil": hasil,
            "profit_loss": round(profit, 2),
            "catatan": "",
        }
        
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        extra_columns = [column for column in df.columns if column not in TRACK_COLUMNS]
        df[TRACK_COLUMNS + extra_columns].to_csv(TRACK_FILE, index=False)
        
        print(f"\n✅ Dicatat:")
        print(f"   {p['home']} {skor_home}-{skor_away} {p['away']}")
        print(f"   Pick: {pick} → {hasil}")
        print(f"   Profit/Loss: {profit:+.2f}x")
    
    except (ValueError, IndexError) as e:
        print(f"❌ Error: {e}")


def show_track():
    """Tampilkan track record"""
    if not os.path.exists(TRACK_FILE):
        print("❌ Belum ada track record")
        return
    
    df = load_track()
    if len(df) == 0:
        print("📭 Track record kosong")
        return
    
    print("\n" + "=" * 70)
    print("📊 TRACK RECORD")
    print("=" * 70)
    print(df.to_string(index=False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    
    total = len(df)
    result_counts = df["hasil"].value_counts()
    print(f"  Total bet:  {total}")
    for result, label in (
        ("WIN", "✅ Menang"),
        ("HALF_WIN", "🟢 Menang setengah"),
        ("LOSE", "❌ Kalah"),
        ("HALF_LOSE", "🟠 Kalah setengah"),
        ("PUSH", "⚖️ Push"),
    ):
        count = int(result_counts.get(result, 0))
        print(f"  {label}: {count} ({count/total*100:.1f}%)")
    
    total_profit = df["profit_loss"].sum()
    avg_profit = df["profit_loss"].mean()
    
    print(f"\n  💰 Total profit: {total_profit:+.2f}x")
    print(f"  💰 Avg profit:   {avg_profit:+.3f}x")
    
    # Per tier
    print(f"\n  📊 Per Tier:")
    for tier in ["🔥 T1", "⚡ T2", "✅ T3"]:
        sub = df[df["tier"] == tier]
        if len(sub) == 0:
            continue
        win_equivalent = (
            len(sub[sub["hasil"] == "WIN"])
            + 0.5 * len(sub[sub["hasil"] == "HALF_WIN"])
        )
        print(
            f"     {tier}: {win_equivalent:.1f}/{len(sub)} "
            f"win-equivalent ({win_equivalent/len(sub)*100:.0f}%)"
        )


def main():
    init_track()
    
    while True:
        print("\n" + "=" * 60)
        print("📋 TRACK RECORD — MENU")
        print("=" * 60)
        print("  [1] Tambah hasil match")
        print("  [2] Lihat track record")
        print("  [3] Exit")
        
        pilih = input("\nPilihan: ").strip()
        
        if pilih == "1":
            add_match_manual()
        elif pilih == "2":
            show_track()
        elif pilih == "3":
            break


if __name__ == "__main__":
    main()
