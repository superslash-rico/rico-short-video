#!/usr/bin/env python3
"""Inventory and clean one completed episode using a fixed, verified file plan."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from datetime import datetime, timezone
import zipfile


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def root_path(value):
    root = Path(value).expanduser().absolute()
    if root.is_symlink() or not root.is_dir() or root == Path(root.anchor) or root == Path.home():
        raise ValueError("Expected one real episode directory, not a root, home or symlink.")
    return root.resolve()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid relative path.")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or relative != rel.as_posix() or any(p in (".", "..") for p in rel.parts):
        raise ValueError("Unsafe or noncanonical path: " + relative)
    target = root.joinpath(*rel.parts)
    parent = root
    for part in rel.parts[:-1]:
        parent /= part
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("Unsafe ancestor: " + relative)
    return target


def outside_output(root, value):
    output = Path(value).expanduser().absolute()
    resolved = output.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("Audit output must be outside the episode directory.")
    if output.is_symlink():
        raise ValueError("Audit output cannot be a symlink.")
    return output


def signature(path, relative, with_hash):
    s = path.lstat()
    entry = {"path": relative, "bytes": s.st_size, "mtime_ns": s.st_mtime_ns,
             "inode": s.st_ino, "device": s.st_dev}
    if stat.S_ISLNK(s.st_mode):
        entry.update({"kind": "symlink", "target": os.readlink(path)})
    elif stat.S_ISREG(s.st_mode):
        entry["kind"] = "file"
        if with_hash:
            entry["sha256"] = digest(path)
    else:
        raise ValueError("Special file needs manual handling: " + relative)
    return entry


def inventory(root, with_hash=False):
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in list(dirs):
            p = base / name
            if p.is_symlink():
                names.append(name)
                dirs.remove(name)
        for name in names:
            p = base / name
            rel = p.relative_to(root).as_posix()
            safe_path(root, rel)
            files.append(signature(p, rel, with_hash))
    files.sort(key=lambda x: x["path"])
    return {"schema_version": 1, "root": str(root), "at": now(), "files": files,
            "file_count": len(files), "logical_bytes": sum(x["bytes"] for x in files)}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".writing")
    if temporary.exists() or temporary.is_symlink():
        raise ValueError("Audit temporary file already exists.")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def make_plan(root, keep_path):
    keep = read_json(keep_path)
    if not isinstance(keep, list) or not keep or len(keep) != len(set(keep)):
        raise ValueError("Keep file must be a nonempty array of unique relative paths.")
    for rel in keep:
        safe_path(root, rel)
    state = inventory(root, with_hash=True)
    existing = {x["path"]: x for x in state["files"]}
    if set(keep) - existing.keys():
        raise ValueError("A protected file is absent.")
    if any(existing[x]["kind"] != "file" for x in keep):
        raise ValueError("Protected deliverables must be real files, not links.")
    return {"schema_version": 1, "root": str(root), "created_at": now(),
            "requires_human_completion": True, "before": state,
            "protected": sorted(keep), "delete": sorted(existing.keys() - set(keep))}


def preflight(root, plan):
    if plan.get("schema_version") != 1 or plan.get("root") != str(root):
        raise ValueError("Plan belongs to a different root or schema.")
    if plan.get("requires_human_completion") is not True or plan["before"]["root"] != str(root):
        raise ValueError("Completion gate or inventory root does not match.")
    original = plan["before"]["files"]
    expected = {x["path"]: x for x in original}
    protected, deletion = plan["protected"], plan["delete"]
    if (not protected or len(protected) != len(set(protected)) or len(deletion) != len(set(deletion))
            or len(original) != len(expected) or set(protected) & set(deletion)
            or set(protected) | set(deletion) != expected.keys()):
        raise ValueError("Protected/deletion lists overlap, repeat or omit files.")
    for rel in expected:
        safe_path(root, rel)
    current = inventory(root, with_hash=True)
    actual = {x["path"]: x for x in current["files"]}
    if actual.keys() != expected.keys():
        raise ValueError("Episode file set changed after planning; nothing deleted.")
    for rel, entry in expected.items():
        if actual[rel] != entry:
            raise ValueError("File changed after planning; nothing deleted: " + rel)
    for rel in protected:
        path = safe_path(root, rel)
        if actual[rel]["kind"] != "file":
            raise ValueError("Protected deliverable must be a regular file.")
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise ValueError("Protected ZIP failed CRC: " + rel)
    return current, expected


def clean(root, plan, result_path, confirmed):
    if not confirmed:
        raise ValueError("Confirm the human has declared this episode complete before cleanup.")
    if result_path.exists():
        raise ValueError("Result already exists; inspect it before another cleanup.")
    before, expected = preflight(root, plan)
    result = {"schema_version": 1, "root": str(root), "started_at": now(),
              "status": "running", "before_file_count": before["file_count"],
              "before_logical_bytes": before["logical_bytes"], "deleted": [],
              "protected": plan["protected"]}
    write_json(result_path, result)
    try:
        for rel in plan["delete"]:
            path = safe_path(root, rel)
            # Recheck identity just before unlink. Never traverse a symlink's target.
            if signature(path, rel, with_hash=False) != {k: v for k, v in expected[rel].items() if k != "sha256"}:
                raise ValueError("File changed during cleanup: " + rel)
            path.unlink()
            result["deleted"].append({"path": rel, "bytes": expected[rel]["bytes"],
                                      "kind": expected[rel]["kind"]})
        for directory, dirs, _ in os.walk(root, topdown=False, followlinks=False):
            for name in dirs:
                p = Path(directory) / name
                if not p.is_symlink() and p.is_dir() and not any(p.iterdir()):
                    p.rmdir()
        after = inventory(root, with_hash=True)
        if {x["path"] for x in after["files"]} != set(plan["protected"]):
            raise ValueError("Final retained set differs from plan.")
        for entry in after["files"]:
            if entry != expected[entry["path"]]:
                raise ValueError("Protected file changed during cleanup: " + entry["path"])
        result.update({"status": "complete", "finished_at": now(),
                       "deleted_count": len(result["deleted"]),
                       "deleted_logical_bytes": sum(x["bytes"] for x in result["deleted"]),
                       "after_file_count": after["file_count"], "after_logical_bytes": after["logical_bytes"],
                       "retained": after["files"]})
    except Exception as exc:
        result.update({"status": "stopped", "error": str(exc), "finished_at": now()})
        write_json(result_path, result)
        raise
    write_json(result_path, result)
    return {k: v for k, v in result.items() if k not in ("deleted", "retained", "protected")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--root", required=True)
    inv.add_argument("--output", required=True)
    inv.add_argument("--hash", action="store_true")
    plan = sub.add_parser("plan")
    plan.add_argument("--root", required=True)
    plan.add_argument("--keep", required=True)
    plan.add_argument("--output", required=True)
    run = sub.add_parser("clean")
    run.add_argument("--root", required=True)
    run.add_argument("--plan", required=True)
    run.add_argument("--result", required=True)
    run.add_argument("--confirmed-complete", action="store_true")
    args = parser.parse_args()
    try:
        root = root_path(args.root)
        if args.command == "clean":
            result = outside_output(root, args.result)
            print(json.dumps(clean(root, read_json(args.plan), result, args.confirmed_complete), ensure_ascii=False))
        else:
            output = outside_output(root, args.output)
            if output.exists():
                raise ValueError("Output exists; use a new audit path.")
            payload = inventory(root, args.hash) if args.command == "inventory" else make_plan(root, args.keep)
            write_json(output, payload)
            print(json.dumps({"output": str(output), "files": len(payload.get("files", payload.get("before", {}).get("files", []))),
                              "delete": len(payload.get("delete", []))}, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
