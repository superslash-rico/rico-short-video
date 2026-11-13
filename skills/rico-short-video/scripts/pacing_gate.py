#!/usr/bin/env python3
"""Check declared shot ranges, coverage and duration for speech-led short videos."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def check(shots, fps, target_seconds=3, max_seconds=5, duration_frames=None, start_frame=0):
    for name, value in (("fps", fps), ("target_seconds", target_seconds), ("max_seconds", max_seconds)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(name + " must be a finite positive number")
    if max_seconds < target_seconds:
        raise ValueError("max_seconds must be at least target_seconds")
    if not integer(start_frame) or start_frame < 0:
        raise ValueError("start_frame must be a nonnegative integer")
    if duration_frames is not None and (not integer(duration_frames) or duration_frames <= 0):
        raise ValueError("duration_frames must be a positive integer")
    if not isinstance(shots, list) or not shots:
        raise ValueError("shots must be a nonempty array")

    errors = []
    durations = []
    over_target = []
    over_limit = []
    ids = set()
    expected_start = start_frame
    for row in shots:
        if not isinstance(row, dict):
            errors.append("Each shot must be an object")
            continue
        shot_id = row.get("id")
        if not isinstance(shot_id, str) or not shot_id.strip() or shot_id in ids:
            errors.append("Each shot needs a unique nonempty id")
            continue
        ids.add(shot_id)
        start, end = row.get("startFrame"), row.get("endFrame")
        if not integer(start) or not integer(end) or start < 0 or end <= start:
            errors.append(shot_id + " has invalid startFrame/endFrame")
            continue
        if start != expected_start:
            errors.append(shot_id + " has a gap, overlap or out-of-order range")
        expected_start = end
        seconds = (end - start) / fps
        item = {"id": shot_id, "startFrame": start, "endFrame": end, "seconds": seconds}
        durations.append(item)
        if seconds > target_seconds + 1e-9:
            over_target.append(item)
        if seconds > max_seconds + 1e-9:
            over_limit.append(item)
            errors.append(shot_id + " exceeds the maximum shot duration")
    if duration_frames is not None and expected_start != start_frame + duration_frames:
        errors.append("Shot ranges do not end at the declared scope boundary")

    return {
        "ok": not errors,
        "errors": errors,
        "fps": fps,
        "target_seconds": target_seconds,
        "max_seconds": max_seconds,
        "start_frame": start_frame,
        "duration_frames": duration_frames,
        "shots_checked": len(durations),
        "max_observed_seconds": max((row["seconds"] for row in durations), default=None),
        "shots": durations,
        "over_target": over_target,
        "over_limit": over_limit,
        "scope": "Declared frame ranges and timing only. Visual changes, reading and continuous playback need actual review."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shots", required=True)
    parser.add_argument("--fps", type=float, required=True)
    parser.add_argument("--target-seconds", type=float, default=3)
    parser.add_argument("--max-seconds", type=float, default=5)
    parser.add_argument("--duration-frames", type=int)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        source = Path(args.shots).expanduser().resolve()
        content = source.read_bytes()
        result = check(json.loads(content), args.fps, args.target_seconds, args.max_seconds,
                       args.duration_frames, args.start_frame)
        result["source_file"] = str(source)
        result["source_sha256"] = hashlib.sha256(content).hexdigest()
        if args.output:
            output = Path(args.output).expanduser().resolve()
            skill_root = Path(__file__).resolve().parents[1]
            if output == skill_root or skill_root in output.parents or output == source:
                raise ValueError("Save a separate task report outside the installed Skill")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    except (OSError, ValueError, TypeError) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
