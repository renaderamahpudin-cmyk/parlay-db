"""
ANALISA PER ERA — Cek Apakah Pola Berubah
"""
import pandas as pd
import os

INTL_DIR = "data/international"


def load_goals():
    df = pd.read_csv(f"{INTL_DIR}/goalscorers.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["minute"])
    df["year"] = df["date"].dt.year
    return df


def bucket_era(year):
    if year < 1960:
        return "Pre-1960"
    elif year < 1980:
        return "1960-1979"
    elif year < 2000:
        return "1980-1999"
    elif year < 2010:
        return "2000-2009"
    elif year < 2020:
        return "2010-2019"
    else:
        return "2020+"


def distribusi_per_era(df):
    print("\n" + "=" * 70)
    print("📊 DISTRIBUSI GOL PER ERA")
    print("=" * 70)
    
    df["era"] = df["year"].apply(bucket_era)
    
    eras = ["Pre-1960", "1960-1979", "1980-1999", "2000-2009", "2010-2019", "2020+"]
    
    bins = [0, 15, 30, 45, 60, 75, 90, 130]
    labels = ["1-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]
    df["range_15"] = pd.cut(df["minute"], bins=bins, labels=labels, right=True)
    
    print(f"\n  {'Era':12} {'Total':>8} {'1-15':>7} {'16-30':>7} {'31-45':>7} {'46-60':>7} {'61-75':>7} {'76-90':>7}")
    print(f"  {'-'*78}")
    
    for era in eras:
        d = df[df["era"] == era]
        if len(d) == 0:
            continue
        
        total = len(d)
        counts = {}
        for label in labels:
            counts[label] = (d["range_15"] == label).sum()
            pct = (counts[label] / total * 100)
            counts[label] = f"{pct:.1f}%"
        
        print(f"  {era:12} {total:>8,} "
              f"{counts['1-15']:>7} {counts['16-30']:>7} {counts['31-45']:>7} "
              f"{counts['46-60']:>7} {counts['61-75']:>7} {counts['76-90']:>7}")


def total_gol_per_match_per_era(df):
    """Estimasi total gol per match (via goalscorers)"""
    print("\n" + "=" * 70)
    print("📊 RATA-RATA GOL PER MATCH PER ERA")
    print("=" * 70)
    
    df["era"] = df["year"].apply(bucket_era)
    
    # Group by (date, home, away) untuk hitung gol per match
    match_gols = df.groupby(["date", "home_team", "away_team"]).size().reset_index(name="total_gol")
    match_gols["year"] = match_gols["date"].dt.year
    match_gols["era"] = match_gols["year"].apply(bucket_era)
    
    eras = ["Pre-1960", "1960-1979", "1980-1999", "2000-2009", "2010-2019", "2020+"]
    
    print(f"\n  {'Era':12} {'Jumlah Match':>15} {'Rata Gol':>10} {'Max Gol':>10}")
    print(f"  {'-'*50}")
    
    for era in eras:
        d = match_gols[match_gols["era"] == era]
        if len(d) == 0:
            continue
        print(f"  {era:12} {len(d):>15,} {d['total_gol'].mean():>10.2f} {d['total_gol'].max():>10}")


def top_scorer_per_era(df, n=5):
    """Top scorer per era"""
    print("\n" + "=" * 70)
    print(f"⚽ TOP {n} SCORER PER ERA")
    print("=" * 70)
    
    df["era"] = df["year"].apply(bucket_era)
    
    eras = ["Pre-1960", "1960-1979", "1980-1999", "2000-2009", "2010-2019", "2020+"]
    
    for era in eras:
        d = df[df["era"] == era]
        if len(d) == 0:
            continue
        
        print(f"\n  🔹 {era} ({len(d):,} gol):")
        top = d.groupby("scorer").size().sort_values(ascending=False).head(n)
        for i, (nama, gol) in enumerate(top.items(), 1):
            print(f"     {i}. {nama[:35]:35} {gol:>4}")


def main():
    print("=" * 70)
    print("⚽ ANALISA PER ERA")
    print("=" * 70)
    
    df = load_goals()
    print(f"\n  ✅ Total gol: {len(df):,}")
    print(f"  ✅ Rentang: {df['year'].min()} s/d {df['year'].max()}")
    
    distribusi_per_era(df)
    total_gol_per_match_per_era(df)
    top_scorer_per_era(df, n=5)
    
    print("\n" + "=" * 70)
    print("✅ SELESAI")
    print("=" * 70)


if __name__ == "__main__":
    main()
