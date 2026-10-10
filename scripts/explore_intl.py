"""
EKSPLORASI DATA INTERNATIONAL
"""
import pandas as pd
import os

INTL_DIR = "data/international"

print("=" * 70)
print("📊 EKSPLORASI DATA INTERNATIONAL")
print("=" * 70)

# 1. Results
print("\n[1] RESULTS.CSV — Hasil pertandingan")
print("-" * 70)
df = pd.read_csv(f"{INTL_DIR}/results.csv")
print(f"  Total baris: {len(df):,}")
print(f"  Kolom: {list(df.columns)}")
print(f"  Rentang: {df['date'].min()} s/d {df['date'].max()}")
print(f"  Total tim unik: {df['home_team'].nunique() + df['away_team'].nunique()}")
print(f"  Tim unik: {df['home_team'].nunique()}")
print(f"\n  Contoh 3 baris terakhir:")
print(df.tail(3).to_string())

# 2. Goalscorers
print("\n[2] GOALSCORERS.CSV — Pencetak gol")
print("-" * 70)
gs = pd.read_csv(f"{INTL_DIR}/goalscorers.csv")
print(f"  Total baris: {len(gs):,}")
print(f"  Kolom: {list(gs.columns)}")
print(f"  Rentang: {gs['date'].min()} s/d {gs['date'].max()}")
print(f"  Total pemain unik: {gs['scorer'].nunique()}")
print(f"\n  Contoh 3 baris terakhir:")
print(gs.tail(3).to_string())

# 3. Shootouts
print("\n[3] SHOOTOUTS.CSV — Adu penalti")
print("-" * 70)
sh = pd.read_csv(f"{INTL_DIR}/shootouts.csv")
print(f"  Total baris: {len(sh):,}")
print(f"  Kolom: {list(sh.columns)}")
print(f"\n  Contoh 3 baris:")
print(sh.head(3).to_string())

# 4. Former names
print("\n[4] FORMER_NAMES.CSV — Nama tim lama")
print("-" * 70)
fn = pd.read_csv(f"{INTL_DIR}/former_names.csv")
print(f"  Total baris: {len(fn):,}")
print(f"  Kolom: {list(fn.columns)}")
print(f"\n  Contoh 5 baris:")
print(fn.head(5).to_string())

print("\n" + "=" * 70)
