#!/usr/bin/env python3
"""Check shot-limit boundaries, scope coverage and supported frame rates."""
import unittest
import pacing_gate as gate


class PacingTests(unittest.TestCase):
    def test_five_seconds_is_allowed(self):
        rows = [{"id": "A", "startFrame": 0, "endFrame": 150}]
        result = gate.check(rows, 30, duration_frames=150)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["over_target"]), 1)

    def test_one_frame_over_limit_is_reported(self):
        result = gate.check([{"id": "A", "startFrame": 0, "endFrame": 151}], 30)
        self.assertFalse(result["ok"])
        self.assertEqual(result["over_limit"][0]["id"], "A")

    def test_fractional_fps_uses_actual_seconds(self):
        rows = [{"id": "A", "startFrame": 0, "endFrame": 150}]
        self.assertFalse(gate.check(rows, 29.97)["ok"])
        self.assertTrue(gate.check(rows, 60)["ok"])

    def test_scope_may_start_inside_master_timeline(self):
        rows = [{"id": "A", "startFrame": 100, "endFrame": 190},
                {"id": "B", "startFrame": 190, "endFrame": 280}]
        self.assertTrue(gate.check(rows, 30, start_frame=100, duration_frames=180)["ok"])
        self.assertFalse(gate.check(rows, 30, start_frame=100, duration_frames=181)["ok"])

    def test_gaps_and_overlaps_are_reported(self):
        for second_start in (89, 91):
            rows = [{"id": "A", "startFrame": 0, "endFrame": 90},
                    {"id": "B", "startFrame": second_start, "endFrame": 180}]
            self.assertFalse(gate.check(rows, 30)["ok"])

    def test_duplicate_ids_and_boolean_frames_are_rejected(self):
        rows = [{"id": "A", "startFrame": 0, "endFrame": 90},
                {"id": "A", "startFrame": 90, "endFrame": 180}]
        self.assertFalse(gate.check(rows, 30)["ok"])
        self.assertFalse(gate.check([{"id": "A", "startFrame": False, "endFrame": 90}], 30)["ok"])

    def test_invalid_fps_and_empty_data_are_rejected(self):
        with self.assertRaises(ValueError):
            gate.check([], 30)
        with self.assertRaises(ValueError):
            gate.check([{"id": "A", "startFrame": 0, "endFrame": 90}], float("nan"))


if __name__ == "__main__":
    unittest.main()
