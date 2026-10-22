#!/usr/bin/env python3
"""Validate recorded visual review and file identities; never judge skin pixels."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

SOURCE_CHECKS = {
    "correct_color_interpretation", "single_color_conversion", "natural_skin",
    "highlight_color_and_detail", "normal_midtones", "face_100_percent",
    "phone_size", "representative_encode_reviewed",
}
FINAL_CHECKS = {
    "same_frame_comparison", "natural_skin", "highlight_color_and_detail",
    "normal_midtones", "face_100_percent", "phone_size",
    "no_additional_whitening", "color_tags_and_range",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def inside(root, value):
    require(text(value), "Missing file path")
    rel = Path(value)
    require(not rel.is_absolute() and ".." not in rel.parts, "Use task-relative paths")
    target = (root / rel).resolve()
    require(target.is_relative_to(root), "File escapes task directory")
    require(target.is_file(), "Missing file: " + value)
    return target


def file_record(root, item, cache):
    require(isinstance(item, dict), "Expected file record {path, sha256}")
    path = inside(root, item.get("path"))
    sha = item.get("sha256")
    require(isinstance(sha, str) and len(sha) == 64, "Missing SHA256: " + str(path))
    if path not in cache:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        cache[path] = digest.hexdigest()
    require(cache[path] == sha, "Stale file/review SHA256: " + str(path))


def evidence(root, records, roles, cache):
    require(isinstance(records, list) and bool(records), "Missing visual evidence")
    for item in records:
        file_record(root, item, cache)
    found = {item.get("role") for item in records}
    require(roles <= found, "Missing evidence roles: " + ", ".join(sorted(roles - found)))


def reviewed_gate(gate, checks):
    require(gate.get("status") == "pass", "Visual review is not pass")
    require(text(gate.get("reviewed_at")), "Missing actual review time")
    values = gate.get("checks", {})
    for key in sorted(checks):
        require(values.get(key) == "pass", "Incomplete/failed check: " + key)


def optional_scene(value, label):
    require(isinstance(value, dict), "Missing " + label)
    require(value.get("status") in {"checked", "not_present"}, "Unreviewed " + label)
    require(text(value.get("notes")), "Explain inspected scene/absence: " + label)


def validate(root, report, stage):
    root = Path(root).expanduser().resolve(strict=True)
    require(root.is_dir(), "Task root must be a directory")
    require(report.get("schema_version") == 1, "Unsupported schema_version")
    require(isinstance(report.get("applies"), bool), "applies must be explicit")
    if not report["applies"]:
        require(text(report.get("not_applicable_reason")), "Explain why no human-color review applies")
        return {"status": "not_applicable", "reason": report["not_applicable_reason"]}
    cache = {}
    artifacts = report.get("artifacts", {})
    required = ["source", "working", "representative_encode"] + (["final"] if stage == "final" else [])
    for name in required:
        records = artifacts.get(name)
        require(isinstance(records, list) and bool(records), "Missing artifact: " + name)
        for item in records:
            file_record(root, item, cache)
    source = report.get("source_gate", {})
    reviewed_gate(source, SOURCE_CHECKS)
    require(source.get("input_classification") in {"hdr", "sdr", "mixed"}, "Input color is unresolved")
    for key in ["pipeline_notes", "reference_display"]:
        require(text(source.get(key)), "Missing " + key)
    for label in ["opening", "brightest_face", "middle", "ending"]:
        points = source.get("coverage", {}).get(label)
        require(isinstance(points, list) and bool(points), "Missing sample coverage: " + label)
        require(all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v >= 0 for v in points), "Invalid source timestamp")
    optional_scene(source.get("near_or_light_change"), "near/light-change scene")
    evidence(root, source.get("evidence"), {"probe", "full_frame", "face_detail"}, cache)
    if stage == "final":
        final = report.get("final_gate", {})
        reviewed_gate(final, FINAL_CHECKS)
        require(text(final.get("source_timeline_mapping")), "Missing same-frame source/timeline mapping")
        optional_scene(final.get("transitions"), "transition entry/middle/exit")
        roles = {"same_frame_full", "same_frame_face"}
        if final["transitions"]["status"] == "checked":
            roles.add("transitions")
        evidence(root, final.get("evidence"), roles, cache)
    return {"status": "evidence_valid", "stage": stage, "files_checked": len(cache),
            "scope": "Recorded review and SHA256 only; visual judgment is performed by the reviewer."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--report", default="工程/色彩验收.json")
    parser.add_argument("--stage", choices=["source", "final"], required=True)
    args = parser.parse_args()
    try:
        root = Path(args.root).expanduser().resolve(strict=True)
        report = json.loads(inside(root, args.report).read_text(encoding="utf-8"))
        require(isinstance(report, dict), "Report must be an object")
        result = validate(root, report, args.stage)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print("COLOR REVIEW BLOCKED: " + str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
