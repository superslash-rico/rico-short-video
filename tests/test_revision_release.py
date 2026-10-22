import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'skills/rico-short-video/scripts/revision.py'


class ReleaseRevision(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rico-revision-test-')
        self.root = Path(self.temp.name) / 'skill'
        (self.root / 'scripts').mkdir(parents=True)
        shutil.copy2(SOURCE, self.root / 'scripts/revision.py')
        (self.root / 'SKILL.md').write_text('---\nname: rico-short-video\ndescription: Test fixture.\n---\nInitial workflow.\n')
        (self.root / 'revision.json').write_text(json.dumps({'revision':47,'distribution_version':'0.3.0','source_revision':43}))
        self.validator = Path(self.temp.name) / 'validate.py'
        self.validator.write_text('print("fixture validation passed")\n')
        self.history = Path(self.temp.name) / 'history'

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args):
        return subprocess.run([sys.executable,str(self.root/'scripts/revision.py'),*args],text=True,capture_output=True)

    def begin(self):
        result=self.command('begin','--history-root',str(self.history),'--reason','Release fixture')
        self.assertEqual(result.returncode,0,result.stderr)
        return Path(json.loads(result.stdout)['snapshot'])

    def finish(self, snapshot, version='0.4.0'):
        return self.command('finish','--snapshot',str(snapshot),'--summary','Updated workflow',
                            '--validator',str(self.validator),'--distribution-version',version)

    def test_release_metadata_and_snapshot_agree_and_repeat_is_idempotent(self):
        snapshot=self.begin()
        (self.root/'SKILL.md').write_text((self.root/'SKILL.md').read_text()+'New workflow detail.\n')
        result=self.finish(snapshot)
        self.assertEqual(result.returncode,0,result.stderr)
        revision=json.loads((self.root/'revision.json').read_text())
        self.assertEqual((revision['revision'],revision['source_revision'],revision['distribution_version']),(48,48,'0.4.0'))
        record=json.loads((snapshot/'record.json').read_text())
        self.assertEqual(record['after_hashes']['revision.json'],hashlib.sha256((self.root/'revision.json').read_bytes()).hexdigest())
        self.assertEqual((snapshot/'after/revision.json').read_bytes(),(self.root/'revision.json').read_bytes())
        repeat=self.finish(snapshot)
        self.assertEqual(repeat.returncode,0,repeat.stderr)
        self.assertTrue(json.loads(repeat.stdout)['already_recorded'])
        mismatch=self.finish(snapshot,'0.5.0')
        self.assertNotEqual(mismatch.returncode,0)
        self.assertEqual((snapshot/'after/revision.json').read_bytes(),(self.root/'revision.json').read_bytes())

    def test_invalid_version_does_not_mutate_metadata_or_create_after_snapshot(self):
        snapshot=self.begin()
        before=(self.root/'revision.json').read_bytes()
        result=self.finish(snapshot,'invalid release')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.root/'revision.json').read_bytes(),before)
        self.assertFalse((snapshot/'after').exists())

    def test_version_only_change_does_not_silently_succeed(self):
        snapshot=self.begin()
        before=(self.root/'revision.json').read_bytes()
        result=self.finish(snapshot)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.root/'revision.json').read_bytes(),before)
        self.assertFalse((snapshot/'after').exists())

    def test_legacy_finish_keeps_previous_distribution_metadata(self):
        snapshot=self.begin()
        (self.root/'SKILL.md').write_text((self.root/'SKILL.md').read_text()+'Local-only update.\n')
        result=self.command('finish','--snapshot',str(snapshot),'--summary','Local update','--validator',str(self.validator))
        self.assertEqual(result.returncode,0,result.stderr)
        revision=json.loads((self.root/'revision.json').read_text())
        self.assertEqual((revision['revision'],revision['source_revision'],revision['distribution_version']),(48,43,'0.3.0'))


if __name__=='__main__':
    unittest.main()
