#!/usr/bin/env python3
"""Check short-video hook/motion evidence coverage and version binding, not taste."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = ("camera", "perspective", "element_scale")
SCENE_CHECKS = ("mobile_readability", "occlusion_and_extrema", "adjacent_handoff")
HOOK_CHECKS = ("subject_and_semantic_readability", "visual_extrema_and_edges", "settle_and_handoff")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def span(value):
    if isinstance(value, dict):
        value = [value.get("start_inclusive"), value.get("end_exclusive")]
    return value if isinstance(value, list) and len(value) == 2 and all(integer(x) for x in value) and 0 <= value[0] < value[1] else None


def evidence(row, base, errors, label):
    if not isinstance(row, dict) or not text(row.get("file")) or not text(row.get("sha256")):
        errors.append(label + ": actual file/sha256 required")
        return None
    path = (base / row["file"]).resolve()
    if not path.is_file() or digest(path) != row["sha256"]:
        errors.append(label + ": file missing or changed")
        return None
    return path


def scene_rows(handoff):
    rows = handoff.get("scenes")
    if not isinstance(rows, list) or not rows or any(not isinstance(x, dict) for x in rows):
        raise ValueError("Current handoff scenes required")
    result = {}
    for s in rows:
        sid = s.get("scene_id")
        if not text(sid) or sid in result or span(s.get("master_range_frames")) is None:
            raise ValueError("Unique scene IDs and actual master frame ranges required")
        result[sid] = s
    return result


def dimension_template():
    return {"decision": None, "purpose_or_reason": None, "mechanism": None,
            "state_kind": "motion", "status": "not_checked", "finding": None,
            "sample_ids": [], "state_units": None, "states": [],
            "visible_change": "not_checked", "transform_space": None, "object_id": None}


def make_template(handoff):
    master = handoff.get("master") or {}
    rows = scene_rows(handoff)
    return {
        "schema_version": 1, "template_only": True,
        "output": {"file": None, "sha256": None, "canvas_size": master.get("canvas_size"), "fps": master.get("fps")},
        "opening": {"decision": None, "mode": "motion_hook", "purpose_or_reason": None, "range_frames": None,
                    "full_frame_end_exclusive": None, "first_animation_frame": None, "sfx_omission_reason": None,
                    "visual_mechanism": None, "semantic_events": [], "sfx_events": [],
                    "mix_preview": {"file": None, "sha256": None},
                    "checks": {k: "not_checked" for k in HOOK_CHECKS},
                    "audition": {"status": "not_checked", "scope": None, "finding": None},
                    "binding_evidence": {"file": None, "sha256": None}, "source_files": [], "frame_samples": [], "settle_frame": None, "unchanged_approved_reference": None},
        "scenes": [
            {"scene_id": sid, "master_range_frames": s["master_range_frames"],
             "source_files": [], "binding_evidence": {"file": None, "sha256": None},
             "samples": [],
             **{k: dimension_template() for k in DIMENSIONS},
             "checks": {k: {"status": "not_checked", "finding": None} for k in SCENE_CHECKS}}
            for sid, s in rows.items()],
        "sample_template": {"id": None, "master_frame": None, "phase": None,
                            "origin": "encoded_output", "file": None, "sha256": None},
        "state_template": {"sample_id": None, "values": []},
        "semantic_event_template": {"master_frame": None, "spoken_anchor": None, "visual_action": None},
        "sfx_event_template": {"master_frame": None, "role": None, "source": None, "rights": None,
                              "file": None, "sha256": None},
        "scope": "Assistant fills actual records. Evidence/coverage checks do not certify pixels, listening, aesthetics or user approval."
    }


def check(handoff_path, report_path):
    hp, rp = Path(handoff_path).resolve(), Path(report_path).resolve()
    h, d = json.loads(hp.read_text()), json.loads(rp.read_text())
    errors, pending, warnings = [], [], []
    if h.get("template_only") is not False:
        errors.append("Actual handoff required")
    rows = scene_rows(h)
    if d.get("schema_version") != 1 or d.get("template_only") is not False:
        errors.append("Fill actual report; template is not evidence")
    bound = evidence((h.get("motion_review") or {}).get("report"), hp.parent, errors, "handoff/motion-review")
    if bound and bound != rp:
        errors.append("Handoff points to a different report")
    out = d.get("output") or {}
    evidence(out, rp.parent, errors, "current-output")
    master = h.get("master") or {}
    canvas = out.get("canvas_size")
    if not isinstance(canvas, list) or len(canvas) != 2 or any(not integer(x) or x <= 0 for x in canvas):
        errors.append("Actual positive output canvas required")
    fps = out.get("fps")
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        errors.append("Actual positive output fps required")
    if out.get("canvas_size") != master.get("canvas_size") or out.get("fps") != master.get("fps"):
        errors.append("Output canvas/fps differs from master handoff")
    submitted = d.get("scenes")
    if not isinstance(submitted, list) or any(not isinstance(x, dict) for x in submitted):
        raise ValueError("Report scenes must be an object array")
    by = {x.get("scene_id"): x for x in submitted}
    if len(by) != len(submitted) or set(by) != set(rows):
        errors.append("Current handoff/report scene coverage differs or IDs repeat")
    for sid, row in by.items():
        if sid not in rows:
            continue
        label = str(sid)
        frame_span = span(row.get("master_range_frames"))
        if frame_span != span(rows[sid]["master_range_frames"]):
            errors.append(label + ": stale master frame range")
        sources = row.get("source_files")
        if not isinstance(sources, list) or not sources:
            errors.append(label + ": current actual code/support source files required")
        else:
            for source in sources:
                evidence(source, rp.parent, errors, label + "/source")
        evidence(row.get("binding_evidence"), rp.parent, errors, label + "/native-binding")
        samples = row.get("samples")
        if not isinstance(samples, list) or any(not isinstance(x, dict) for x in samples):
            errors.append(label + ": sample array required")
            samples = []
        sample_by = {x.get("id"): x for x in samples}
        if len(samples) < 2 or len(sample_by) != len(samples) or any(not text(x) for x in sample_by):
            errors.append(label + ": at least two uniquely named encoded frame samples required")
        frames = []
        for sample in samples:
            f = sample.get("master_frame")
            if not integer(f) or not frame_span or not frame_span[0] <= f < frame_span[1]:
                errors.append(label + ": encoded frame outside current scene")
            else:
                frames.append(f)
            if sample.get("origin") != "encoded_output" or not text(sample.get("phase")):
                errors.append(label + ": actual encoded origin and observed phase required")
            evidence(sample, rp.parent, errors, label + "/sample")
        if len(set(frames)) < 2:
            errors.append(label + ": different-time motion/reading evidence required")
        if samples and len({x.get("sha256") for x in samples}) < 2 and any((row.get(k) or {}).get("decision") == "required" and (row.get(k) or {}).get("state_kind") == "motion" for k in DIMENSIONS):
            errors.append(label + ": identical frame bytes cannot show declared motion")
        for dimension in DIMENSIONS:
            value = row.get(dimension) or {}
            dl = label + "/" + dimension
            if not text(value.get("purpose_or_reason")) or not text(value.get("finding")):
                errors.append(dl + ": actual purpose/reason and observation required")
            ids = value.get("sample_ids")
            if not isinstance(ids, list) or not ids or any(not text(x) or x not in sample_by for x in ids):
                errors.append(dl + ": link actual sample IDs")
                ids = []
            decision = value.get("decision")
            if decision == "not_applicable":
                if value.get("status") != "not_applicable":
                    errors.append(dl + ": exemption status/reason must be explicit")
                continue
            if decision != "required" or value.get("status") != "pass" or not text(value.get("mechanism")):
                errors.append(dl + ": required dimension not reviewed/implemented")
            if dimension == "element_scale" and (value.get("transform_space") != "object" or not text(value.get("object_id"))):
                errors.append(dl + ": identify the independently transformed object; camera scale is not object scale")
            states = value.get("states")
            valid = []
            for state in states if isinstance(states, list) else []:
                nums = state.get("values") if isinstance(state, dict) else None
                if not isinstance(state, dict) or state.get("sample_id") not in ids or not isinstance(nums, list) or not nums or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in nums):
                    errors.append(dl + ": actual finite state values linked to samples required")
                else:
                    valid.append((state["sample_id"], nums))
            if len({x[0] for x in valid}) < 2 or not text(value.get("state_units")):
                errors.append(dl + ": two time-linked states and units required")
            elif len({len(x[1]) for x in valid}) != 1:
                errors.append(dl + ": inconsistent state vector")
            elif value.get("state_kind") == "stable_depth" and dimension == "perspective":
                if not any(abs(x) > 1e-6 for _, nums in valid for x in nums):
                    errors.append(dl + ": zero depth/tilt does not show stable perspective")
            elif value.get("state_kind") != "motion" or not any(abs(a - b) > 1e-6 for _, nums in valid[1:] for a, b in zip(valid[0][1], nums)):
                errors.append(dl + ": constant state cannot evidence motion")
            if value.get("visible_change") != "clear" and not (dimension == "perspective" and value.get("state_kind") == "stable_depth" and value.get("visible_change") == "stable_readable_depth"):
                errors.append(dl + ": perceptible change needs actual visual review; micro movement is not a substitute")
        if all((row.get(k) or {}).get("decision") == "not_applicable" for k in DIMENSIONS):
            warnings.append(label + ": all dimensions held/flat; manually confirm scene-specific exemption")
        for key in SCENE_CHECKS:
            value = (row.get("checks") or {}).get(key) or {}
            if value.get("status") != "pass" or not text(value.get("finding")):
                errors.append(label + "/" + key + ": actual scene review missing")
    opening = d.get("opening") or {}
    if not text(opening.get("purpose_or_reason")):
        errors.append("opening: explicit purpose or limited-change scope reason required")
    if opening.get("decision") == "not_applicable":
        if not text(opening.get("unchanged_approved_reference")):
            errors.append("opening: exemption needs unchanged/approved opening or scope evidence")
    elif opening.get("decision") == "required":
        mode = opening.get("mode", "motion_hook")
        if mode not in ("motion_hook", "live_scene_first"):
            errors.append("opening: unsupported mode")
        opening_sources = opening.get("source_files")
        if not isinstance(opening_sources, list) or not opening_sources:
            errors.append("opening: current media/effect/caption source files required")
        else:
            for source in opening_sources:
                evidence(source, rp.parent, errors, "opening/source")
        os = span(opening.get("range_frames"))
        if not os or os[0] != 0 or not text(opening.get("visual_mechanism")):
            errors.append("opening: actual opening range/visual mechanism required")
        if mode == "live_scene_first":
            full_end = opening.get("full_frame_end_exclusive")
            if not integer(full_end) or not os or not os[0] < full_end <= os[1]:
                errors.append("opening: actual full-frame display end required")
            first_animation = opening.get("first_animation_frame")
            if first_animation is not None:
                if not integer(first_animation) or not integer(full_end) or first_animation < full_end:
                    errors.append("opening: animation starts before full-frame display ends")
        settle = opening.get("settle_frame")
        if not integer(settle) or not os or not os[0] <= settle < os[1]:
            errors.append("opening: actual settle/return frame required")
        hook_samples = opening.get("frame_samples")
        if not isinstance(hook_samples, list) or len(hook_samples) < 2:
            errors.append("opening: encoded extrema/return frame evidence required")
        else:
            hook_frames = []
            for sample in hook_samples:
                if not isinstance(sample, dict):
                    errors.append("opening: frame sample must be an object")
                    continue
                f = sample.get("master_frame")
                if not integer(f) or not os or not os[0] <= f < os[1] or sample.get("origin") != "encoded_output" or not text(sample.get("phase")):
                    errors.append("opening: actual encoded opening frame/phase required")
                else:
                    hook_frames.append(f)
                evidence(sample, rp.parent, errors, "opening/frame")
            if len(set(hook_frames)) < 2:
                errors.append("opening: different-time encoded frame evidence required")
        events = opening.get("semantic_events")
        if not isinstance(events, list) or not events:
            errors.append("opening: semantic/visual anchor events required")
        else:
            for e in events:
                if not isinstance(e, dict) or not integer(e.get("master_frame")) or not os or not os[0] <= e["master_frame"] < os[1] or not text(e.get("spoken_anchor")) or not text(e.get("visual_action")):
                    errors.append("opening: invalid semantic anchor")
        effects = opening.get("sfx_events")
        if not isinstance(effects, list):
            errors.append("opening: sound events must be an array")
        elif not effects:
            if mode != "live_scene_first" or not text(opening.get("sfx_omission_reason")):
                errors.append("opening: actual event-aligned sound effects required or explain live-scene sound arrangement")
        else:
            for e in effects:
                if not isinstance(e, dict):
                    errors.append("opening: sound event must be an object")
                    continue
                if not integer(e.get("master_frame")) or not os or not os[0] <= e["master_frame"] < os[1] or any(not text(e.get(k)) for k in ("role", "source", "rights")):
                    errors.append("opening: sound anchor/source/rights missing")
                evidence(e, rp.parent, errors, "opening/sfx")
        evidence(opening.get("mix_preview"), rp.parent, errors, "opening/actual-mix-preview")
        evidence(opening.get("binding_evidence"), rp.parent, errors, "opening/native-binding")
        for key in HOOK_CHECKS:
            if (opening.get("checks") or {}).get(key) != "pass":
                errors.append("opening/" + key + ": actual visual review missing")
        audition = opening.get("audition") or {}
        if audition.get("status") not in ("pass", "partial", "not_checked") or not text(audition.get("scope")) or not text(audition.get("finding")):
            errors.append("opening: record actual listening scope/status")
        elif audition["status"] != "pass":
            pending.append("Opening subjective listening remains " + audition["status"] + "; do not claim it passed")
    else:
        errors.append("opening: required or explicit not_applicable decision required")
    return {"ok": not errors, "errors": errors, "pending_review": pending, "warnings": warnings,
            "scenes_checked": len(rows), "scope": "Coverage, state declarations and current bytes only; no automatic pixel/aesthetic/listening judgment or user approval."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("prepare")
    c.add_argument("--handoff", required=True)
    c.add_argument("--output", required=True)
    c = sub.add_parser("check")
    c.add_argument("--handoff", required=True)
    c.add_argument("--report", required=True)
    a = p.parse_args()
    try:
        if a.command == "prepare":
            dest = Path(a.output).expanduser().resolve()
            if dest == ROOT or ROOT in dest.parents or dest.exists():
                raise ValueError("Write a new task report outside the installed Skill; do not overwrite evidence")
            result = make_template(json.loads(Path(a.handoff).read_text()))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            result = {"ok": True, "file": str(dest), "state": "template-not-checked"}
        else:
            result = check(a.handoff, a.report)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as e:
        result = {"ok": False, "errors": [str(e)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
