import os
import requests
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

# URL base untuk extra leagues
BASE_EXTRA = "https://football-data.co.uk/new"
DATA_DIR = "data/football_data_extra"

# Liga extra prioritas
LEAGUES_EXTRA = {
    "ARG": "Argentina Primera",
    "AUT": "Austria Bundesliga",
    "BRA": "Brazil Serie A",
    "CHN": "China Super League",
    "DNK": "Denmark Superliga",
    "FIN": "Finland Veikkausliiga",
    "IRL": "Ireland Premier Division",
    "JPN": "Japan J-League",
    "MEX": "Mexico Liga MX",
    "NOR": "Norway Eliteserien",
    "POL": "Poland Ekstraklasa",
    "ROU": "Romania Liga 1",
    "RUS": "Russia Premier League",
    "SWE": "Sweden Allsvenskan",
    "SWI": "Switzerland Super League",
    "USA": "USA MLS",
}


def download_extra():
    os.makedirs(DATA_DIR, exist_ok=True)
    all_dfs = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
    }

    total = len(LEAGUES_EXTRA)
    for i, (code, nama) in enumerate(LEAGUES_EXTRA.items(), 1):
        url = f"{BASE_EXTRA}/{code}.csv"
        path = f"{DATA_DIR}/{code}.csv"

        try:
            # PENTING: pakai allow_redirects=True (default requests)
            r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            r.raise_for_status()

            # Parse
            df = pd.read_csv(pd.io.common.StringIO(r.text), on_bad_lines="skip", low_memory=False)

            if len(df) == 0:
                print(f"  [{i}/{total}] {code:5} → EMPTY")
                continue

            # Normalisasi nama kolom
            df.columns = df.columns.str.strip()

            # Tambah metadata
            df["LeagueCode"] = code
            df["LeagueName"] = nama

            # Simpan
            df.to_csv(path, index=False)
            all_dfs.append(df)

            # Hitung musim
            if "Season" in df.columns:
                seasons = df["Season"].nunique()
                range_season = f"{df['Season'].min()}-{df['Season'].max()}"
            else:
                seasons = "?"
                range_season = "?"

            print(f"  [{i}/{total}] {code:5} → {len(df):>6} baris | "
                  f"{seasons} musim ({range_season})")

        except Exception as e:
            print(f"  [{i}/{total}] {code:5} → ERROR: {e}")

    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        merged.to_csv(f"{DATA_DIR}/all_extra.csv", index=False)
        print(f"\n✅ TOTAL extra: {len(merged):,} baris")
        print(f"   Liga: {merged['LeagueName'].nunique()}")
        if "Season" in merged.columns:
            print(f"   Musim: {merged['Season'].nunique()}")
        return merged
    return None


if __name__ == "__main__":
    print("=" * 70)
    print("DOWNLOAD EXTRA LEAGUES")
    print("=" * 70)
    print(f"Liga: {len(LEAGUES_EXTRA)}")
    print(f"URL base: {BASE_EXTRA}\n")

    df = download_extra()

    if df is not None:
        print("\n" + "=" * 70)
        print("RINGKASAN PER LIGA")
        print("=" * 70)
        summary = df.groupby("LeagueName").agg(
            total_baris=("Home", "count"),
            musim=("Season", "nunique") if "Season" in df.columns else ("Home", "count")
        ).sort_values("total_baris", ascending=False)
        print(summary.to_string())
