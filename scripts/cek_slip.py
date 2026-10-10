"""
CEK SLIP MANUAL — Input match, cek H2H + prediksi
"""
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)


def load_db():
    data = []
    try:
        df = pd.read_csv("data/football_data/all_football_data.csv", low_memory=False)
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
        df = df[["HomeTeam", "AwayTeam", "FTHG", "FTAG", "League", "Date"]].copy()
        df.columns = ["home", "away", "hg", "ag", "league", "date"]
        data.append(df)
    except: pass
    
    try:
        df = pd.read_csv("data/football_data_extra/all_extra.csv", low_memory=False)
        df = df.dropna(subset=["Home", "Away", "HG", "AG"])
        df = df[["Home", "Away", "HG", "AG", "LeagueName", "Date"]].copy()
        df.columns = ["home", "away", "hg", "ag", "league", "date"]
        data.append(df)
    except: pass
    
    df = pd.concat(data, ignore_index=True)
    df["hg"] = pd.to_numeric(df["hg"], errors="coerce")
    df["ag"] = pd.to_numeric(df["ag"], errors="coerce")
    return df.dropna(subset=["hg", "ag"])


def cek_match(df, home, away):
    def cocok(nama_db, nama_cari):
        if not isinstance(nama_db, str):
            return False
        n = nama_db.lower().strip()
        c = nama_cari.lower().strip()
        if n == c:
            return True
        if len(n) >= 5 and len(c) >= 5:
            if n in c or c in n:
                return True
        return False
    
    mask = (
        (df["home"].apply(lambda x: cocok(x, home)) &
         df["away"].apply(lambda x: cocok(x, away))) |
        (df["home"].apply(lambda x: cocok(x, away)) &
         df["away"].apply(lambda x: cocok(x, home)))
    )
    return df[mask]


def main():
    print("=" * 60)
    print("🔍 CEK SLIP MANUAL")
    print("=" * 60)
    
    home = input("\nMasukkan tim HOME: ").strip()
    away = input("Masukkan tim AWAY: ").strip()
    
    if not home or not away:
        print("❌ Tim tidak boleh kosong")
        return
    
    print(f"\n⏳ Cek H2H {home} vs {away}...")
    
    df = load_db()
    h2h = cek_match(df, home, away)
    
    if len(h2h) == 0:
        print(f"\n❌ Tidak ada H2H {home} vs {away}")
        return
    
    # Statistik
    print(f"\n✅ H2H: {len(h2h)} pertemuan")
    
    # Hasil
    def hasil(row):
        if home.lower() in row["home"].lower():
            h, a = row["hg"], row["ag"]
        else:
            h, a = row["ag"], row["hg"]
        if h > a: return "W"
        elif h < a: return "L"
        return "D"
    
    h2h = h2h.copy()
    h2h["hasil"] = h2h.apply(hasil, axis=1)
    
    w = (h2h["hasil"] == "W").sum()
    d = (h2h["hasil"] == "D").sum()
    l = (h2h["hasil"] == "L").sum()
    total = len(h2h)
    
    print(f"\n📊 Hasil dari {home}:")
    print(f"   Win:  {w} ({w/total*100:.1f}%)")
    print(f"   Draw: {d} ({d/total*100:.1f}%)")
    print(f"   Lose: {l} ({l/total*100:.1f}%)")
    
    # Gol
    if home.lower() in h2h.iloc[0]["home"].lower():
        gol_a = h2h["hg"].tolist()
        gol_b = h2h["ag"].tolist()
    else:
        gol_a = h2h["ag"].tolist()
        gol_b = h2h["hg"].tolist()
    
    avg_a = sum(gol_a)/len(gol_a)
    avg_b = sum(gol_b)/len(gol_b)
    
    print(f"\n⚽ Rata-rata gol:")
    print(f"   {home}: {avg_a:.2f}")
    print(f"   {away}: {avg_b:.2f}")
    print(f"   Total: {avg_a + avg_b:.2f}")
    
    # Probabilitas O/U
    total_gols = [g1 + g2 for g1, g2 in zip(gol_a, gol_b)]
    print(f"\n📊 Probabilitas O/U:")
    for line in [1.5, 2.5, 3.0, 3.5, 4.0]:
        over = sum(1 for g in total_gols if g > line)
        rate = (over / len(total_gols)) * 100
        print(f"   Over {line}: {rate:.1f}%")
    
    # 10 terakhir
    print(f"\n📋 10 pertemuan terakhir:")
    for _, r in h2h.tail(10).iterrows():
        print(f"   {r['date']} | {r['home']} {int(r['hg'])}-{int(r['ag'])} {r['away']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
