"""
ANALISA MENIT GOL — Latihan Teknik
Sumber: data/international/goalscorers.csv
"""
import pandas as pd
import os

INTL_DIR = "data/international"

def load_goals():
    df = pd.read_csv(f"{INTL_DIR}/goalscorers.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["minute"])
    return df


def distribusi_per_15menit(df):
    """Distribusi gol per 15 menit"""
    print("\n" + "=" * 70)
    print("📊 DISTRIBUSI GOL PER 15 MENIT")
    print("=" * 70)
    
    bins = [0, 15, 30, 45, 60, 75, 90, 120]
    labels = ["1-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]
    
    df["range_15"] = pd.cut(df["minute"], bins=bins, labels=labels, right=True)
    
    distribusi = df["range_15"].value_counts().sort_index()
    total = distribusi.sum()
    
    print(f"\n  Total gol: {total:,}\n")
    print(f"  {'Menit':10} {'Jumlah':>10} {'Persen':>10}")
    print(f"  {'-'*32}")
    
    for label in labels:
        count = distribusi.get(label, 0)
        pct = (count / total) * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:10} {count:>10,} {pct:>9.1f}%  {bar}")


def top_scorer(df, n=20):
    """Top N pencetak gol sepanjang masa"""
    print("\n" + "=" * 70)
    print(f"⚽ TOP {n} PENCETAK GOL SEPANJANG MASA")
    print("=" * 70)
    
    top = df.groupby("scorer").size().sort_values(ascending=False).head(n)
    
    print(f"\n  {'No':>3} {'Pemain':35} {'Gol':>6}")
    print(f"  {'-'*48}")
    for i, (nama, gol) in enumerate(top.items(), 1):
        print(f"  {i:>3} {nama[:35]:35} {gol:>6}")


def tim_galak_babak1(df, n=20):
    """Tim dengan gol babak 1 terbanyak"""
    print("\n" + "=" * 70)
    print(f"🔥 TOP {n} TIM GALAK BABAK 1 (menit 1-45)")
    print("=" * 70)
    
    babak1 = df[df["minute"] <= 45]
    top = babak1.groupby("team").size().sort_values(ascending=False).head(n)
    
    print(f"\n  {'No':>3} {'Tim':30} {'Gol Babak 1':>12}")
    print(f"  {'-'*48}")
    for i, (nama, gol) in enumerate(top.items(), 1):
        print(f"  {i:>3} {nama[:30]:30} {gol:>12}")


def tim_clutch(df, n=20):
    """Tim dengan gol 76-90 terbanyak (clutch)"""
    print("\n" + "=" * 70)
    print(f"💪 TOP {n} TIM CLUTCH (menit 76-90)")
    print("=" * 70)
    
    clutch = df[(df["minute"] >= 76) & (df["minute"] <= 90)]
    top = clutch.groupby("team").size().sort_values(ascending=False).head(n)
    
    print(f"\n  {'No':>3} {'Tim':30} {'Gol 76-90':>12}")
    print(f"  {'-'*48}")
    for i, (nama, gol) in enumerate(top.items(), 1):
        print(f"  {i:>3} {nama[:30]:30} {gol:>12}")


def pola_gol_per_tim(df, tim_list):
    """Pola gol per babak untuk tim tertentu"""
    print("\n" + "=" * 70)
    print("📊 POLA GOL PER BABAK (Tim Terpilih)")
    print("=" * 70)
    
    print(f"\n  {'Tim':20} {'Babak 1':>10} {'Babak 2':>10} {'Late (76+)':>12} {'Total':>10}")
    print(f"  {'-'*68}")
    
    for tim in tim_list:
        dt = df[df["team"] == tim]
        if len(dt) == 0:
            continue
        
        babak1 = (dt["minute"] <= 45).sum()
        babak2 = ((dt["minute"] > 45) & (dt["minute"] <= 90)).sum()
        late = ((dt["minute"] >= 76) & (dt["minute"] <= 90)).sum()
        total = len(dt)
        
        pct_b1 = (babak1 / total * 100) if total > 0 else 0
        pct_b2 = (babak2 / total * 100) if total > 0 else 0
        pct_late = (late / total * 100) if total > 0 else 0
        
        print(f"  {tim[:20]:20} {babak1:>4} ({pct_b1:>3.0f}%) {babak2:>4} ({pct_b2:>3.0f}%) "
              f"{late:>4} ({pct_late:>3.0f}%) {total:>6}")


def main():
    print("=" * 70)
    print("⚽ ANALISA MENIT GOL — DATA INTERNASIONAL")
    print("=" * 70)
    
    df = load_goals()
    print(f"\n  ✅ Total gol: {len(df):,}")
    print(f"  ✅ Rentang: {df['date'].min().date()} s/d {df['date'].max().date()}")
    print(f"  ✅ Tim unik: {df['team'].nunique()}")
    print(f"  ✅ Pemain unik: {df['scorer'].nunique()}")
    
    # 1. Distribusi
    distribusi_per_15menit(df)
    
    # 2. Top scorer
    top_scorer(df, n=20)
    
    # 3. Tim galak babak 1
    tim_galak_babak1(df, n=15)
    
    # 4. Tim clutch
    tim_clutch(df, n=15)
    
    # 5. Pola gol tim besar
    tim_list = ["Brazil", "Argentina", "France", "England", "Spain",
                "Germany", "Italy", "Netherlands", "Portugal", "Belgium"]
    pola_gol_per_tim(df, tim_list)
    
    print("\n" + "=" * 70)
    print("✅ ANALISA SELESAI")
    print("=" * 70)


if __name__ == "__main__":
    main()
