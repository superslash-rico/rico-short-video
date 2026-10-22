#!/usr/bin/env python3
"""Snapshot this skill before edits; validate and record a content revision."""
import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def files_at(root):
    found = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(p.startswith(".") or p == "__pycache__" for p in rel.parts):
            continue
        # Public preview videos/images stay in the skill, identified by a hashed manifest.
        # Revisions snapshot instructions, metadata and licenses, not another 900 MB per edit.
        if rel.parts[:3] in {("assets", "motiongit", "covers"), ("assets", "motiongit", "previews")}:
            continue
        selected = str(rel) in {"SKILL.md", "revision.json"} or rel.parts[0] in {
            "agents", "references", "scripts", "assets", "templates"
        }
        if selected and path.is_symlink():
            raise ValueError("Tracked skill resource is a symlink: " + str(rel))
        if selected and path.is_file():
            found[rel.as_posix()] = path
    return found


def hashes(files):
    return {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}


def copy_files(files, target):
    target.mkdir(parents=True, exist_ok=False)
    for name, path in files.items():
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())


def begin(args):
    history = Path(args.history_root).expanduser().resolve()
    if history == ROOT or ROOT in history.parents:
        raise ValueError("History must be outside the skill directory.")
    tracked = files_at(ROOT)
    revision = read_json(ROOT / "revision.json")["revision"]
    history.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    snapshot = history / (stamp + "-" + uuid.uuid4().hex[:8])
    snapshot.mkdir()
    copy_files(tracked, snapshot / "before")
    write_json(snapshot / "record.json", {
        "schema_version": 1,
        "skill_root": str(ROOT),
        "created_at": now(),
        "reason": args.reason,
        "before_revision": revision,
        "before_hashes": hashes(tracked),
        "status": "pending"
    })
    print(json.dumps({"snapshot": str(snapshot), "revision": revision}, ensure_ascii=False))


def finish(args):
    version = getattr(args, "distribution_version", None)
    if version is not None and not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError("Invalid distribution version.")
    snapshot = Path(args.snapshot).expanduser().resolve()
    record_path = snapshot / "record.json"
    record = read_json(record_path)
    if Path(record["skill_root"]).resolve() != ROOT:
        raise ValueError("Snapshot belongs to a different skill directory.")
    current = files_at(ROOT)
    current_hashes = hashes(current)
    if record["status"] in {"applied", "no_change"}:
        if version is not None and read_json(ROOT / "revision.json").get("distribution_version") != version:
            raise ValueError("Snapshot already finished with another distribution version.")
        if current_hashes != record["after_hashes"]:
            raise ValueError("Skill changed after this revision; begin a new snapshot.")
        print(json.dumps({
            "snapshot": str(snapshot), "status": record["status"],
            "revision": record["after_revision"], "already_recorded": True
        }, ensure_ascii=False))
        return
    before = files_at(snapshot / "before")
    if hashes(before) != record["before_hashes"]:
        raise ValueError("Before snapshot no longer matches its recorded hashes.")
    current_revision = read_json(ROOT / "revision.json")
    if (
        current_revision["revision"] != record["before_revision"]
        or current_hashes.get("revision.json") != record["before_hashes"].get("revision.json")
    ):
        raise ValueError("Revision metadata changed; reconcile other updates before finishing.")
    if (snapshot / "after").exists():
        raise ValueError("An incomplete finish left after files; inspect before retrying.")
    validator = Path(args.validator).expanduser().resolve()
    if not validator.is_file():
        raise ValueError("Official validator was not found.")
    check = subprocess.run(
        [sys.executable, str(validator), str(ROOT)], capture_output=True, text=True
    )
    record["validation"] = {
        "validator": str(validator), "checked_at": now(),
        "exit_code": check.returncode,
        "output": (check.stdout + check.stderr)[-8000:]
    }
    if check.returncode:
        record["status"] = "validation_failed"
        write_json(record_path, record)
        raise ValueError("Validation failed; revision was not advanced.\n" + record["validation"]["output"])
    changed = sorted(
        name for name in set(record["before_hashes"]) | set(current_hashes)
        if name != "revision.json" and record["before_hashes"].get(name) != current_hashes.get(name)
    )
    if version is not None and not changed and current_revision.get("distribution_version") != version:
        raise ValueError("Release metadata requires a resource change in this snapshot.")
    if changed:
        current_revision.update({
            "revision": current_revision["revision"] + 1,
            "updated_at": now(), "last_change": args.summary
        })
        if version is not None:
            current_revision.update({"distribution_version": version, "source_revision": current_revision["revision"]})
        write_json(ROOT / "revision.json", current_revision)
    after = files_at(ROOT)
    copy_files(after, snapshot / "after")
    patch = []
    for name in changed:
        old_bytes = before[name].read_bytes() if name in before else b""
        new_bytes = after[name].read_bytes() if name in after else b""
        try:
            old_text, new_text = old_bytes.decode("utf-8"), new_bytes.decode("utf-8")
            patch.extend(difflib.unified_diff(
                old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                fromfile="before/" + name, tofile="after/" + name
            ))
        except UnicodeDecodeError:
            patch.append("Binary resource changed: " + name + "\n")
    (snapshot / "changes.patch").write_text("".join(patch), encoding="utf-8")
    record.update({
        "status": "applied" if changed else "no_change",
        "finished_at": now(), "summary": args.summary,
        "changed_files": changed,
        "after_revision": current_revision["revision"],
        "after_hashes": hashes(after)
    })
    write_json(record_path, record)
    print(json.dumps({
        "snapshot": str(snapshot), "status": record["status"],
        "revision": current_revision["revision"], "changed_files": changed
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("begin", help="Save this skill before making an edit.")
    start.add_argument("--history-root", required=True)
    start.add_argument("--reason", required=True)
    end = commands.add_parser("finish", help="Validate and record the edited skill.")
    end.add_argument("--snapshot", required=True)
    end.add_argument("--summary", required=True)
    end.add_argument("--validator", required=True)
    end.add_argument("--distribution-version", help="Record this public release and its source revision in the same snapshot.")
    args = parser.parse_args()
    try:
        begin(args) if args.command == "begin" else finish(args)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
