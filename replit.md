# Running the project on Replit

This project is a Python command-line app, not a web server.

## Start the app

Run `python main.py` in the Replit console, or use the configured **Start application** console workflow. The menu supports predictions, saved slips, and walk-forward backtesting.

Predictions fetch the current fixtures and odds from the source used by `scripts/parse_full.py`. They also need the dated match archive at `data/football_data/all_football_data.csv`.

## Run the walk-forward backtest

Run:

```sh
python scripts/backtest_ou_walkforward.py
```

The default holdout is the most recent 20% of distinct match dates. Forecasts only use matches dated before the forecast date, and all matches on a given date are forecast before that date is added to model history. Detailed forecasts and calibration/ROI breakdowns are written to `generated-artifacts/backtest_ou_poisson_walkforward.csv` and `generated-artifacts/backtest_ou_poisson_summary.csv`. Generated output is kept out of Git history.

The archive has consistent historical odds for O/U 2.5, not a full history of Asian total lines. Current predictions support Asian lines and account for pushes and half wins/losses, but historical per-line evaluation is currently limited by that archive.

Install project dependencies with `uv sync` if the Replit Python environment needs to be restored.

