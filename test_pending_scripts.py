import contextlib
from datetime import date, timedelta
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import auto_track
import backtest_ou_walkforward
import save_draft
from parlay_builder_v3 import analisa_ou, bandingkan_opsi, bandingkan_opsi_2
from pick_policy import is_eligible_ou_pick
from settlement import settle_pick
from ou_model import WalkForwardModel, settlement_distribution


def build_recent_form_model():
    model = WalkForwardModel()
    rows = []
    for index in range(40):
        rows.append({
            "date": (date(2024, 1, 1) + timedelta(days=index)).isoformat(),
            "home": f"League Home {index}",
            "away": f"League Away {index}",
            "hg": 2,
            "ag": 1,
            "league": "Test",
            "hst": 5,
            "ast": 3,
        })
    for index in range(8):
        rows.extend([
            {
                "date": f"2024-03-{index + 1:02d}",
                "home": "Home FC",
                "away": f"Home Opponent {index}",
                "hg": (2, 2, 1, 2, 1, 2, 1, 2)[index],
                "ag": (0, 1, 1, 0, 1, 0, 1, 1)[index],
                "league": "Test",
                "hst": 5,
                "ast": 3,
            },
            {
                "date": f"2024-03-{index + 1:02d}",
                "home": f"Away Opponent {index}",
                "away": "Away FC",
                "hg": (1, 2, 1, 1, 2, 1, 2, 1)[index],
                "ag": (1, 1, 2, 1, 1, 2, 1, 1)[index],
                "league": "Test",
                "hst": 4,
                "ast": 4,
            },
        ])
    for row in sorted(rows, key=lambda item: item["date"]):
        model.update(row)
    return model


class SettlementTests(unittest.TestCase):
    def test_full_push_on_integer_line(self):
        self.assertEqual(settle_pick("UNDER 3.0", 2, 1, 2.0), ("PUSH", 0.0))

    def test_quarter_line_half_win_and_half_loss(self):
        self.assertEqual(settle_pick("UNDER 3.25", 2, 1, 2.0), ("HALF_WIN", 0.5))
        self.assertEqual(settle_pick("OVER 3.25", 2, 1, 2.0), ("HALF_LOSE", -0.5))
        self.assertEqual(settle_pick("UNDER 3.75", 2, 2, 2.0), ("HALF_LOSE", -0.5))

    def test_one_x_two_draw_and_score_validation(self):
        self.assertEqual(settle_pick("DRAW", 1, 1, 3.2), ("WIN", 2.2))
        self.assertEqual(auto_track.tentukan_hasil("DRAW", 2, 1, 1, 3.2), ("WIN", 2.2))
        with self.assertRaises(ValueError):
            settle_pick("HOME", 1, 1, 1.0)
        with self.assertRaises(ValueError):
            settle_pick("UNDER 2.5", -1, 1, 2.0)


class ValueComparisonTests(unittest.TestCase):
    def setUp(self):
        self.goal_pairs = [(0, 0), (0, 1), (1, 2), (1, 2)]
        self.ou_lines = [
            {"line": 2.5, "over": 1.9, "under": 1.9},
            {"line": 3.0, "over": 1.9, "under": 2.0},
        ]

    def test_pushes_are_not_counted_as_under_wins(self):
        options = bandingkan_opsi(
            self.goal_pairs, self.ou_lines, 2.5, 3.2, 2.8,
            home_win_rate=25, draw_rate=25, away_win_rate=50,
        )
        under_three = next(item for item in options if item.get("pick") == "UNDER 3")
        self.assertEqual(under_three["prob"], 100.0)
        self.assertEqual(under_three["push_rate"], 50.0)
        self.assertEqual(under_three["expected_profit"], 0.5)

    def test_market_line_25_does_not_override_better_line(self):
        _, top_ou, blind_spot = bandingkan_opsi_2(
            self.goal_pairs, self.ou_lines, 2.5, 3.2, 2.8,
            home_win_rate=25, draw_rate=25, away_win_rate=50,
        )
        self.assertEqual(top_ou["pick"], "UNDER 3")
        self.assertTrue(blind_spot["ada_di_market"])

    def test_ou_analyzer_returns_only_positive_gap_market_pick(self):
        result = analisa_ou(
            None,
            "Home FC",
            [
                {"line": 2.5, "over": 3.4, "under": 1.3},
                {"line": 3.0, "over": 3.2, "under": 1.35},
            ],
            away_web="Away FC",
            model=build_recent_form_model(),
            as_of="2024-06-01",
            league="Test",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["pick_jenis"], "OU")
        self.assertGreaterEqual(result["value_gap"], 5)
        self.assertGreater(result["pick_expected_return"], 0)
        self.assertEqual(result["home_form_n"], 8)
        self.assertEqual(result["away_form_n"], 8)
        self.assertNotIn("top_1x2", result)
        self.assertNotIn("btts_rate", result)
        self.assertTrue(is_eligible_ou_pick(result))

    def test_ou_analyzer_skips_negative_and_small_gaps(self):
        result = analisa_ou(
            None,
            "Home FC",
            [{"line": 2.5, "over": 1.01, "under": 1.01}],
            away_web="Away FC",
            model=build_recent_form_model(),
            as_of="2024-06-01",
            league="Test",
        )
        self.assertIsNone(result)

    def test_policy_rejects_non_ou_and_negative_gap(self):
        self.assertTrue(is_eligible_ou_pick({
            "pick_jenis": "OU", "pick": "OVER 2.5",
            "pick_odds": 1.9, "pick_conf": 60, "value_gap": 5,
        }))
        for invalid in (
            {"pick_jenis": "OU", "pick": "OVER 2.5", "pick_odds": 1.54, "value_gap": -3},
            {"pick_jenis": "1X2", "pick": "AWAY", "pick_odds": 3.0, "value_gap": 23.8},
            {"pick_jenis": "BTTS", "pick": "BTTS YES", "pick_odds": 1.8, "value_gap": 12},
        ):
            self.assertFalse(is_eligible_ou_pick(invalid))


class WalkForwardBacktestTests(unittest.TestCase):
    def setUp(self):
        import pandas as pd

        raw = []
        for index in range(1, 6):
            raw.append({
                "Date": f"2024-01-{index:02d}",
                "HomeTeam": "A",
                "AwayTeam": f"Home Opp {index}",
                "FTHG": 2,
                "FTAG": 1,
                "League": "Test",
                "Avg>2.5": 1.9,
                "Avg<2.5": 1.9,
                "HST": 5,
                "AST": 3,
            })
            raw.append({
                "Date": f"2024-02-{index:02d}",
                "HomeTeam": f"Away Opp {index}",
                "AwayTeam": "B",
                "FTHG": 1,
                "FTAG": 1,
                "League": "Test",
                "Avg>2.5": 1.9,
                "Avg<2.5": 1.9,
                "HST": 3,
                "AST": 4,
            })
        raw.extend([
            {"Date": "2024-03-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 2, "FTAG": 1, "League": "Test",
             "Avg>2.5": 1.9, "Avg<2.5": 1.9},
            # Same-day and future meetings must not leak into a June 1 forecast.
            {"Date": "2024-06-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 0, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.9, "Avg<2.5": 1.9},
            {"Date": "2024-06-01", "HomeTeam": "B", "AwayTeam": "A",
             "FTHG": 5, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.9, "Avg<2.5": 1.9},
            {"Date": "01/07/2024", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 0, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.9, "Avg<2.5": 1.9},
        ])
        self.matches = backtest_ou_walkforward.prepare_matches(
            pd.DataFrame(raw)
        )

    def test_dates_parse_iso_and_day_first_without_mixing_formats(self):
        import pandas as pd

        june_match = self.matches.loc[
            (self.matches["home"] == "A")
            & (self.matches["away"] == "B")
            & (self.matches["date"] == pd.Timestamp("2024-06-01"))
        ]
        july_match = self.matches.loc[
            (self.matches["home"] == "A")
            & (self.matches["away"] == "B")
            & (self.matches["date"] == pd.Timestamp("2024-07-01"))
        ]
        self.assertEqual(len(june_match), 1)
        self.assertEqual(len(july_match), 1)

    def test_walk_forward_excludes_same_day_h2h_and_future_results(self):
        result = backtest_ou_walkforward.run_backtest(
            self.matches, test_start="2024-06-01"
        )
        target = result["details"].loc[
            (result["details"]["home"] == "A")
            & (result["details"]["away"] == "B")
            & (result["details"]["date"] == "2024-06-01")
        ].iloc[0]
        self.assertEqual(target["h2h_before"], 1)
        self.assertEqual(target["home_form_n"], 6)
        self.assertEqual(target["away_form_n"], 6)
        self.assertIsNotNone(target["model_over25_pct"])


class AsianPoissonTests(unittest.TestCase):
    def test_poisson_distribution_is_normalized(self):
        settlement = settlement_distribution(1.7, 1.2, "OVER", 2.5, 1.9)
        self.assertAlmostEqual(
            sum(settlement["total_pmf"]), 1.0, places=10
        )

    def test_quarter_line_reports_half_win_and_half_loss(self):
        over = settlement_distribution(1.5, 1.3, "OVER", 2.75, 2.0)
        under = settlement_distribution(1.5, 1.3, "UNDER", 2.75, 2.0)
        self.assertGreater(over["half_win"], 0)
        self.assertGreater(under["half_loss"], 0)
        self.assertEqual(over["push"], 0)
        self.assertAlmostEqual(sum(
            over[key] for key in
            ("full_win", "half_win", "push", "half_loss", "full_loss")
        ), 1.0, places=9)

    def test_market_probabilities_are_no_vig_and_integer_push_is_counted(self):
        from ou_model import compare_market_line

        result = compare_market_line(1.5, 1.2, 3.0, 1.9, 2.1)
        self.assertAlmostEqual(
            result["market_over_no_vig_pct"]
            + result["market_under_no_vig_pct"],
            100,
        )
        self.assertGreater(result["over"]["push"], 0)
        self.assertIsInstance(result["under"]["expected_return"], float)


class PendingDraftTests(unittest.TestCase):
    def test_auto_track_excludes_non_ou_predictions_but_keeps_legacy_ou(self):
        valid_pick = {
            "liga": "TEST LEAGUE",
            "home": "Home FC",
            "away": "Away FC",
            "waktu": "20:00",
            "pick": "OVER 2.5",
            "pick_jenis": "OU",
            "pick_conf": 65,
            "pick_odds": 1.9,
            "value_gap": 8,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                os.makedirs("output")
                Path("output/best_pick.json").write_text(json.dumps([
                    valid_pick,
                    {**valid_pick, "pick": "AWAY", "pick_jenis": "1X2"},
                    {**valid_pick, "pick": "BTTS YES", "pick_jenis": "BTTS"},
                ]), encoding="utf-8")
                self.assertEqual(
                    [p["pick"] for p in auto_track.load_picks()],
                    ["OVER 2.5"],
                )

                legacy_ou = {key: value for key, value in valid_pick.items()
                             if key not in {"pick_jenis", "pick_conf", "pick_odds", "value_gap"}}
                Path("output/draft_pending.json").write_text(json.dumps({
                    "pending_auto": [
                        legacy_ou,
                        {**valid_pick, "pick": "AWAY", "pick_jenis": "1X2"},
                    ],
                }), encoding="utf-8")
                Path("output/best_pick.json").write_text("[]", encoding="utf-8")
                self.assertEqual(
                    [p["pick"] for p in auto_track.load_picks()],
                    ["OVER 2.5"],
                )
            finally:
                os.chdir(original_cwd)

    def test_draft_preserves_original_pick_when_daily_file_changes(self):
        pick = {
            "liga": "TEST LEAGUE",
            "home": "Home FC",
            "away": "Away FC",
            "waktu": "20:00",
            "pick": "UNDER 3.25",
            "pick_jenis": "OU",
            "pick_conf": 64.5,
            "pick_odds": 1.95,
            "pick_implied": 51.3,
            "value_gap": 13.2,
            "skor": 300,
            "tier": "⚡ T2",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                os.makedirs("output")
                Path("output/best_pick.json").write_text(
                    json.dumps([
                        pick,
                        {
                            **pick, "home": "Home 1X2", "away": "Away 1X2",
                            "pick": "AWAY", "pick_jenis": "1X2", "value_gap": 20,
                        },
                    ]), encoding="utf-8"
                )
                Path("output/mapping_liga.json").write_text(
                    json.dumps({"TEST LEAGUE": {"id": 123}}), encoding="utf-8"
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    save_draft.main()

                draft = json.loads(Path("output/draft_pending.json").read_text(encoding="utf-8"))
                self.assertEqual(len(draft["pending_auto"]), 1)
                self.assertEqual(draft["pending_auto"][0]["pick_jenis"], "OU")

                Path("output/best_pick.json").write_text("[]", encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    save_draft.main()

                pending = auto_track.load_picks()
                self.assertEqual(len(pending), 1)
                self.assertEqual(pending[0]["pick"], "UNDER 3.25")
                self.assertEqual(pending[0]["pick_odds"], 1.95)
                self.assertEqual(pending[0]["pick_conf"], 64.5)
                Path("output/best_pick.json").unlink()
                self.assertEqual(auto_track.load_picks()[0]["pick"], "UNDER 3.25")
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
