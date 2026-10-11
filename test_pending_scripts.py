import contextlib
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
        import pandas as pd

        h2h = pd.DataFrame([
            {"home": "Home FC", "away": "Away FC", "hg": home, "ag": away}
            for home, away in ((2, 1), (1, 2), (3, 1), (2, 2), (2, 0))
        ])
        result = analisa_ou(h2h, "Home FC", [
            {"line": 2.5, "over": 1.2, "under": 3.5},
            {"line": 3.0, "over": 1.5, "under": 2.5},
            {"line": 3.5, "over": 3.0, "under": 1.9},
        ])
        self.assertIsNotNone(result)
        self.assertEqual(result["pick_jenis"], "OU")
        self.assertGreaterEqual(result["value_gap"], 5)
        self.assertNotIn("top_1x2", result)
        self.assertNotIn("btts_rate", result)
        self.assertTrue(is_eligible_ou_pick(result))

    def test_ou_analyzer_skips_negative_and_small_gaps(self):
        import pandas as pd

        h2h = pd.DataFrame([
            {"home": "Home FC", "away": "Away FC", "hg": home, "ag": away}
            for home, away in ((2, 1), (1, 2), (3, 1), (2, 2), (2, 0))
        ])
        result = analisa_ou(h2h, "Home FC", [
            {"line": 2.5, "over": 1.2, "under": 3.5},
            {"line": 3.0, "over": 1.5, "under": 2.5},
            {"line": 3.5, "over": 2.2, "under": 1.7},
        ])
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

        self.matches = backtest_ou_walkforward.prepare_matches(pd.DataFrame([
            {"Date": "2024-01-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 3, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            {"Date": "2024-02-01", "HomeTeam": "B", "AwayTeam": "A",
             "FTHG": 0, "FTAG": 1, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            {"Date": "2024-03-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 3, "FTAG": 1, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            {"Date": "2024-04-01", "HomeTeam": "B", "AwayTeam": "A",
             "FTHG": 1, "FTAG": 2, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            {"Date": "2024-05-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 4, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            # A same-day result and a future result must not leak into June 1.
            {"Date": "2024-06-01", "HomeTeam": "B", "AwayTeam": "A",
             "FTHG": 0, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            {"Date": "2024-06-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 2, "FTAG": 1, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
            {"Date": "2024-07-01", "HomeTeam": "A", "AwayTeam": "B",
             "FTHG": 0, "FTAG": 0, "League": "Test",
             "Avg>2.5": 1.5, "Avg<2.5": 2.5},
        ]))

    def test_h2h_excludes_same_day_target_and_future_results(self):
        from datetime import datetime

        index = backtest_ou_walkforward.build_h2h_index(self.matches)
        count, over_count = backtest_ou_walkforward.history_summary_before(
            index, "A", "B", datetime(2024, 6, 1)
        )
        self.assertEqual(count, 5)
        self.assertEqual(over_count, 4)

    def test_walk_forward_pick_uses_prior_h2h_and_real_market_odds(self):
        import pandas as pd

        index = backtest_ou_walkforward.build_h2h_index(self.matches)
        target = self.matches.loc[
            (self.matches["date"] == pd.Timestamp("2024-06-01"))
            & (self.matches["home"] == "A")
        ].iloc[0]
        result = backtest_ou_walkforward.evaluate_fixture(target, index)
        self.assertEqual(result["h2h_before"], 5)
        self.assertEqual(result["model_over25_pct"], 80.0)
        self.assertEqual(result["pick"], "OVER 2.5")
        self.assertEqual(result["market_source"], "Avg")
        self.assertEqual(result["market_odds"], 1.5)
        self.assertTrue(result["won"])


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
