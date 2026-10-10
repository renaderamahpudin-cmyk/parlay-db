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
import save_draft
from parlay_builder_v3 import bandingkan_opsi, bandingkan_opsi_2
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


class PendingDraftTests(unittest.TestCase):
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
                    json.dumps([pick]), encoding="utf-8"
                )
                Path("output/mapping_liga.json").write_text(
                    json.dumps({"TEST LEAGUE": {"id": 123}}), encoding="utf-8"
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    save_draft.main()

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
