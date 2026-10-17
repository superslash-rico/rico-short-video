"""Safety checks for destructive closeout; operates only in temporary folders."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("closeout", Path(__file__).with_name("closeout.py"))
closeout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closeout)


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rico-closeout-test-")
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "episode"
        self.root.mkdir()
        (self.root / "final.mp4").write_bytes(b"keep exact bytes")
        (self.root / "draft.tmp").write_bytes(b"delete")
        self.keep = self.base / "keep.json"
        closeout.write_json(self.keep, ["final.mp4"])
        self.result = self.base / "result.json"

    def tearDown(self):
        self.temp.cleanup()

    def plan(self):
        return closeout.make_plan(self.root, self.keep)

    def test_allowed_cleanup(self):
        outcome = closeout.clean(self.root, self.plan(), self.result, True)
        self.assertEqual(outcome["status"], "complete")
        self.assertFalse((self.root / "draft.tmp").exists())
        self.assertEqual((self.root / "final.mp4").read_bytes(), b"keep exact bytes")

    def test_changed_file_aborts_before_any_deletion(self):
        plan = self.plan()
        (self.root / "final.mp4").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            closeout.clean(self.root, plan, self.result, True)
        self.assertTrue((self.root / "draft.tmp").exists())

    def test_unexpected_file_aborts(self):
        plan = self.plan()
        (self.root / "new.tmp").write_bytes(b"new")
        with self.assertRaises(ValueError):
            closeout.clean(self.root, plan, self.result, True)
        self.assertTrue((self.root / "draft.tmp").exists())

    def test_protected_overlap_aborts(self):
        plan = self.plan()
        plan["delete"].append("final.mp4")
        with self.assertRaises(ValueError):
            closeout.clean(self.root, plan, self.result, True)
        self.assertTrue((self.root / "draft.tmp").exists())

    def test_escaped_path_aborts(self):
        for path in ("../outside", "/tmp/outside", "sub/../final.mp4", "./final.mp4", ""):
            with self.assertRaises(ValueError):
                closeout.safe_path(self.root, path)

    def test_symlink_ancestor_aborts(self):
        external = self.base / "external"
        external.mkdir()
        (self.root / "linked").symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError):
            closeout.safe_path(self.root, "linked/file")

    def test_leaf_symlink_unlinks_without_touching_target(self):
        external = self.base / "external.txt"
        external.write_bytes(b"outside protected")
        (self.root / "leaf-link").symlink_to(external)
        closeout.clean(self.root, self.plan(), self.result, True)
        self.assertFalse((self.root / "leaf-link").is_symlink())
        self.assertEqual(external.read_bytes(), b"outside protected")

    def test_requires_confirmed_completion(self):
        with self.assertRaises(ValueError):
            closeout.clean(self.root, self.plan(), self.result, False)
        self.assertTrue((self.root / "draft.tmp").exists())

    def test_corrupt_protected_zip_aborts(self):
        (self.root / "source.zip").write_bytes(b"not a zip")
        closeout.write_json(self.base / "keep2.json", ["final.mp4", "source.zip"])
        plan = closeout.make_plan(self.root, self.base / "keep2.json")
        with self.assertRaises(closeout.zipfile.BadZipFile):
            closeout.clean(self.root, plan, self.result, True)
        self.assertTrue((self.root / "draft.tmp").exists())


if __name__ == "__main__":
    unittest.main()
