#!/usr/bin/env python3
"""Behavior checks for missed/stale/falsely static motion evidence. No editor mutation."""
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
import motion_gate as gate


def png(color):
    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\0" + bytes(color))) + chunk(b"IEND", b"")


class MotionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        for name, data in {"a.png": png([255, 0, 0]), "b.png": png([0, 0, 255]),
                           "final.mp4": b"test fixture: not a rendered video",
                           "source.jsx": b"export const cameraPose=[1,2];",
                           "binding.json": b'{"effective":[1,2]}', "sound.wav": b"fixture audio"}.items():
            (self.root / name).write_bytes(data)
        self.h = {"template_only": False, "master": {"canvas_size": [1080, 1920], "fps": 25},
                  "scenes": [{"scene_id": "S1", "master_range_frames": [75, 175]}]}
        self.d = gate.make_template(self.h)
        self.d["template_only"] = False
        self.d["output"] = {**self.ref("final.mp4"), "canvas_size": [1080, 1920], "fps": 25}
        self.d["opening"] = {
            "decision": "required", "purpose_or_reason": "Make the opening question legible",
            "range_frames": [0, 75], "settle_frame": 70,
            "frame_samples": [{**self.ref("a.png"), "master_frame": 21, "phase": "extrema", "origin": "encoded_output"},
                              {**self.ref("b.png"), "master_frame": 70, "phase": "return", "origin": "encoded_output"}],
            "visual_mechanism": "protected centre and peripheral slices",
            "semantic_events": [{"master_frame": 21, "spoken_anchor": "question", "visual_action": "focus lands"}],
            "sfx_events": [{**self.ref("sound.wav"), "master_frame": 21, "role": "landing",
                            "source": "fixture", "rights": "test"}],
            "source_files": [self.ref("source.jsx")], "mix_preview": self.ref("final.mp4"), "binding_evidence": self.ref("binding.json"),
            "checks": {k: "pass" for k in gate.HOOK_CHECKS},
            "audition": {"status": "pass", "scope": "fixture only", "finding": "Fixture declaration, no real listening"}
        }
        row = self.d["scenes"][0]
        row["source_files"] = [self.ref("source.jsx")]
        row["binding_evidence"] = self.ref("binding.json")
        row["samples"] = [{**self.ref("a.png"), "id": "overall", "master_frame": 80,
                           "phase": "overall", "origin": "encoded_output"},
                          {**self.ref("b.png"), "id": "detail", "master_frame": 150,
                           "phase": "detail/extrema", "origin": "encoded_output"}]
        for key in gate.DIMENSIONS:
            row[key] = {"decision": "required", "purpose_or_reason": "Inspect the same target",
                        "mechanism": "test transform", "state_kind": "motion", "status": "pass",
                        "finding": "Fixture assertion; not aesthetic validation",
                        "sample_ids": ["overall", "detail"], "state_units": "scale or depth units",
                        "states": [{"sample_id": "overall", "values": [1]},
                                   {"sample_id": "detail", "values": [2]}],
                        "visible_change": "clear", "transform_space": "object", "object_id": "target"}
        row["checks"] = {k: {"status": "pass", "finding": "Fixture scope"} for k in gate.SCENE_CHECKS}

    def ref(self, name):
        return {"file": name, "sha256": gate.digest(self.root / name)}

    def run_check(self):
        report = self.root / "review.json"
        report.write_text(json.dumps(self.d))
        self.h["motion_review"] = {"report": self.ref("review.json")}
        handoff = self.root / "handoff.json"
        handoff.write_text(json.dumps(self.h))
        return gate.check(handoff, report)

    def test_complete_evidence_is_valid(self):
        self.assertTrue(self.run_check()["ok"])

    def test_missing_scene_fails(self):
        self.d["scenes"] = []
        self.assertFalse(self.run_check()["ok"])

    def test_constant_camera_does_not_count_as_motion(self):
        self.d["scenes"][0]["camera"]["states"][1]["values"] = [1]
        self.assertIn("constant state", " ".join(self.run_check()["errors"]))

    def test_unchecked_dimension_fails(self):
        self.d["scenes"][0]["element_scale"]["status"] = "not_checked"
        self.assertFalse(self.run_check()["ok"])

    def test_micro_movement_requires_clear_visual_review(self):
        self.d["scenes"][0]["camera"]["visible_change"] = "subtle_reading"
        self.assertFalse(self.run_check()["ok"])

    def test_stable_depth_is_valid_without_faked_motion(self):
        self.d["scenes"][0]["perspective"].update(
            state_kind="stable_depth", visible_change="stable_readable_depth",
            states=[{"sample_id": "overall", "values": [30, 70]},
                    {"sample_id": "detail", "values": [30, 70]}])
        self.assertTrue(self.run_check()["ok"])

    def test_reasoned_static_screen_overlay_is_allowed(self):
        for key in gate.DIMENSIONS:
            self.d["scenes"][0][key] = {
                "decision": "not_applicable", "status": "not_applicable",
                "purpose_or_reason": "Keep the real click target steady",
                "finding": "Source screen remains legible; use a short highlight",
                "sample_ids": ["overall", "detail"]}
        self.assertTrue(self.run_check()["ok"])
        self.assertTrue(self.run_check()["warnings"])

    def test_unexplained_exemption_fails(self):
        self.d["scenes"][0]["perspective"].update(decision="not_applicable",
                                                 status="not_applicable", purpose_or_reason=None)
        self.assertFalse(self.run_check()["ok"])

    def test_stale_output_fails(self):
        (self.root / "final.mp4").write_bytes(b"new encoding")
        self.assertFalse(self.run_check()["ok"])

    def test_changed_source_fails(self):
        (self.root / "source.jsx").write_bytes(b"new camera")
        self.assertFalse(self.run_check()["ok"])

    def test_old_range_or_outside_frame_fails(self):
        self.d["scenes"][0]["samples"][0]["master_frame"] = 74
        self.assertFalse(self.run_check()["ok"])

    def test_duplicate_terminal_frame_does_not_show_motion(self):
        row = self.d["scenes"][0]
        row["samples"][1].update(self.ref("a.png"))
        self.assertFalse(self.run_check()["ok"])

    def test_missing_opening_sfx_fails(self):
        self.d["opening"]["sfx_events"] = []
        self.assertFalse(self.run_check()["ok"])

    def test_live_scene_first_allows_original_audio_with_explanation(self):
        self.d["opening"].update(
            mode="live_scene_first", full_frame_end_exclusive=75,
            first_animation_frame=75, sfx_events=[],
            sfx_omission_reason="Original speech presents the screen, animation SFX begin at frame 75")
        self.assertTrue(self.run_check()["ok"])

    def test_live_scene_without_sound_explanation_fails(self):
        self.d["opening"].update(
            mode="live_scene_first", full_frame_end_exclusive=75,
            first_animation_frame=75, sfx_events=[])
        self.assertFalse(self.run_check()["ok"])

    def test_live_scene_animation_cannot_enter_during_fullscreen_hold(self):
        self.d["opening"].update(
            mode="live_scene_first", full_frame_end_exclusive=75,
            first_animation_frame=74)
        self.assertFalse(self.run_check()["ok"])

    def test_live_scene_requires_actual_fullscreen_boundary(self):
        self.d["opening"].update(mode="live_scene_first")
        self.assertFalse(self.run_check()["ok"])

    def test_live_scene_can_remain_real_footage_throughout_opening(self):
        self.d["opening"].update(
            mode="live_scene_first", full_frame_end_exclusive=75,
            first_animation_frame=None, sfx_events=[],
            sfx_omission_reason="Keep the original opening speech clear")
        self.assertTrue(self.run_check()["ok"])

    def test_unknown_opening_mode_fails(self):
        self.d["opening"]["mode"] = "unregistered-mode"
        self.assertFalse(self.run_check()["ok"])

    def test_pending_listening_is_explicit_not_approval(self):
        self.d["opening"]["audition"].update(status="not_checked", scope="No playback available", finding="Pending user listen")
        result = self.run_check()
        self.assertTrue(result["ok"])
        self.assertTrue(result["pending_review"])

    def test_camera_scaling_cannot_count_as_object_scaling(self):
        self.d["scenes"][0]["element_scale"]["transform_space"] = "camera"
        self.assertFalse(self.run_check()["ok"])

    def test_zero_depth_cannot_count_as_perspective(self):
        self.d["scenes"][0]["perspective"].update(
            state_kind="stable_depth", visible_change="stable_readable_depth",
            states=[{"sample_id": "overall", "values": [0, 0]},
                    {"sample_id": "detail", "values": [0, 0]}])
        self.assertFalse(self.run_check()["ok"])

    def test_missing_encoded_hook_frames_fails(self):
        self.d["opening"]["frame_samples"] = []
        self.assertFalse(self.run_check()["ok"])

    def test_template_and_missing_occlusion_review_fail(self):
        self.d["template_only"] = True
        self.d["scenes"][0]["checks"]["occlusion_and_extrema"]["status"] = "not_checked"
        self.assertFalse(self.run_check()["ok"])


if __name__ == "__main__":
    unittest.main()
