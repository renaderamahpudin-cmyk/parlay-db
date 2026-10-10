import os
import requests
import pandas as pd
from io import StringIO

BASE_FD = "https://www.football-data.co.uk/mmz4281"
DATA_DIR = "data/football_data"
INTL_DIR = "data/international"

LEAGUES = {
    "E1": "Championship",
    "E0": "Premier League",
    "SP1": "La Liga",
    "SP2": "La Liga 2",
    "I1": "Serie A",
    "I2": "Serie B",
    "D1": "Bundesliga",
    "D2": "Bundesliga 2",
    "F1": "Ligue 1",
    "F2": "Ligue 2",
    "N1": "Eredivisie",
    "N2": "Eerste Divisie",
    "P1": "Primeira Liga",
    "T1": "Super Lig",
    "G1": "Super League Yunani",
}

SEASONS = [
    "0506", "0607", "0708", "0809", "0910",
    "1011", "1112", "1213", "1314", "1415",
    "1516", "1617", "1718", "1819", "1920",
    "2021", "2122", "2223", "2324", "2425", "2526",
    "2627",  # Musim 2026/27 - TAMBAHAN
]


def download_football_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    all_dfs = []
    total = len(SEASONS) * len(LEAGUES)
    n = 0

    for season in SEASONS:
        for code, name in LEAGUES.items():
            n += 1
            url = f"{BASE_FD}/{season}/{code}.csv"
            try:
                r = requests.get(url, timeout=30)
                if r.status_code != 200:
                    print(f"[{n}/{total}] SKIP {season} {code} ({r.status_code})")
                    continue

                df = pd.read_csv(StringIO(r.text), on_bad_lines="skip", low_memory=False)
                if len(df) == 0:
                    print(f"[{n}/{total}] EMPTY {season} {code}")
                    continue

                df["League"] = name
                df["LeagueCode"] = code
                df["Season"] = season
                all_dfs.append(df)

                df.to_csv(f"{DATA_DIR}/{season}_{code}.csv", index=False)
                print(f"[{n}/{total}] OK {season} {code} -> {len(df)} baris")

            except Exception as e:
                print(f"[{n}/{total}] ERR {season} {code}: {e}")

    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        merged.to_csv(f"{DATA_DIR}/all_football_data.csv", index=False)
        print(f"\nTotal football-data: {len(merged)} baris")
        return merged
    return None


def download_international():
    os.makedirs(INTL_DIR, exist_ok=True)
    base = "https://raw.githubusercontent.com/martj42/international_results/refs/heads/master"
    files = ["results.csv", "shootouts.csv", "goalscorers.csv", "former_names.csv"]

    for fname in files:
        try:
            r = requests.get(f"{base}/{fname}", timeout=60)
            r.raise_for_status()
            with open(f"{INTL_DIR}/{fname}", "wb") as f:
                f.write(r.content)
            print(f"[OK] {fname}")
        except Exception as e:
            print(f"[ERR] {fname}: {e}")

    try:
        df = pd.read_csv(f"{INTL_DIR}/results.csv", parse_dates=["date"])
        print(f"\nTotal international: {len(df)} baris")
        return df
    except Exception as e:
        print(f"[ERR] results.csv: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("BUILD DATABASE PARLAY")
    print("=" * 60)
    print(f"Liga: {len(LEAGUES)} | Musim: {len(SEASONS)} | Total file: {len(LEAGUES)*len(SEASONS)}")
    input("\nTekan ENTER untuk mulai...")

    print("\n[1] Download football-data.co.uk")
    fd = download_football_data()

    print("\n[2] Download international_results")
    download_international()

    print("\n" + "=" * 60)
    print("SELESAI")
    print("=" * 60)

    if fd is not None:
        print("\nRingkasan per liga:")
        summary = fd.groupby("League").agg(
            total_match=("HomeTeam", "count"),
            musim=("Season", "nunique")
        ).sort_values("total_match", ascending=False)
        print(summary.to_string())
