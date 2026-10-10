"""
TRACK RECORD — Catat Hasil Prediksi vs Aktual
"""
import json
import os
import pandas as pd
from datetime import datetime

TRACK_FILE = "output/track_record.csv"


def init_track():
    """Bikin file track kalau belum ada"""
    if os.path.exists(TRACK_FILE):
        return
    df = pd.DataFrame(columns=[
        "tanggal", "liga", "home", "away",
        "pick", "conf", "odds", "skor", "tier",
        "skor_home", "skor_away", "total_gol",
        "hasil", "profit_loss", "catatan"
    ])
    df.to_csv(TRACK_FILE, index=False)
    print(f"✅ File baru: {TRACK_FILE}")


def add_match_manual():
    """Input manual hasil match"""
    print("\n" + "=" * 60)
    print("INPUT HASIL MATCH")
    print("=" * 60)
    
    # Load best_pick
    with open("output/best_pick.json") as f:
        picks = json.load(f)
    
    print(f"\nTotal pick tersedia: {len(picks)}")
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
        total_gol = skor_home + skor_away
        
        # Tentukan hasil
        pick = p.get("pick", "")
        conf = p.get("pick_conf", 0)
        odds = p.get("pick_odds", 0)
        
        # Cek hasil
        hasil = "?"
        profit = 0
        
        if "OVER" in pick:
            line = float(pick.replace("OVER ", ""))
            if total_gol > line:
                hasil = "WIN"
                profit = odds - 1 if odds > 0 else 0
            elif total_gol == line:
                hasil = "PUSH"
                profit = 0
            else:
                hasil = "LOSE"
                profit = -1
        
        elif "UNDER" in pick:
            line = float(pick.replace("UNDER ", ""))
            if total_gol < line:
                hasil = "WIN"
                profit = odds - 1 if odds > 0 else 0
            elif total_gol == line:
                hasil = "PUSH"
                profit = 0
            else:
                hasil = "LOSE"
                profit = -1
        
        elif pick == "HOME":
            if skor_home > skor_away:
                hasil = "WIN"
                profit = odds - 1 if odds > 0 else 0
            else:
                hasil = "LOSE"
                profit = -1
        
        elif pick == "AWAY":
            if skor_away > skor_home:
                hasil = "WIN"
                profit = odds - 1 if odds > 0 else 0
            else:
                hasil = "LOSE"
                profit = -1
        
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
            "skor_home": skor_home,
            "skor_away": skor_away,
            "total_gol": total_gol,
            "hasil": hasil,
            "profit_loss": round(profit, 2),
            "catatan": "",
        }
        
        df = pd.read_csv(TRACK_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(TRACK_FILE, index=False)
        
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
    
    df = pd.read_csv(TRACK_FILE)
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
    win = len(df[df["hasil"] == "WIN"])
    lose = len(df[df["hasil"] == "LOSE"])
    push = len(df[df["hasil"] == "PUSH"])
    
    print(f"  Total bet:  {total}")
    print(f"  ✅ Win:     {win} ({win/total*100:.1f}%)")
    print(f"  ❌ Lose:    {lose} ({lose/total*100:.1f}%)")
    print(f"  ⚖️  Push:    {push} ({push/total*100:.1f}%)")
    
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
        w = len(sub[sub["hasil"] == "WIN"])
        print(f"     {tier}: {w}/{len(sub)} win ({w/len(sub)*100:.0f}%)")


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
