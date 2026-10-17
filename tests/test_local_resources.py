import hashlib,importlib.util,io,json,os,sys,tempfile,unittest
from unittest import mock
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/rico-short-video/scripts'))
from setup_local import initialize
from paths import private_file,public_file
from cache_previews import cache_one
spec=importlib.util.spec_from_file_location('public_checker',ROOT/'tools/check_public.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
class Transport:
 def __init__(self,data):self.data=data;self.calls=0
 def open(self,*args,**kwargs):self.calls+=1;return io.BytesIO(self.data)
class LocalResources(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='rico-public-test-');self.state=Path(self.tmp.name).resolve()
 def tearDown(self):self.tmp.cleanup()
 def item(self,data=b'valid'):
  return {'slug':'demo','kind':'cover','url':'https://motiongit.com/media/demo.jpg','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 def test_setup_preserves_existing_profile_and_journal(self):
  initialize(self.state);p=self.state/'profile.json';p.write_text('{"custom":true}');j=self.state/'.motiongit-library/acquisitions.json';original=j.read_bytes();initialize(self.state)
  self.assertEqual(p.read_text(),'{"custom":true}');self.assertEqual(j.read_bytes(),original)
 def test_setup_does_not_replace_profile_symlink(self):
  outside=self.state/'owned.txt';outside.write_text('keep');(self.state/'profile.json').symlink_to(outside);initialize(self.state);self.assertEqual(outside.read_text(),'keep')
 def test_cache_reuses_verified_bytes_without_network(self):
  t=Transport(b'valid');item=self.item();cache_one(item,self.state,t);result=cache_one(item,self.state,t)
  self.assertTrue(result['reused']);self.assertEqual(t.calls,1)
 def test_failed_cache_preserves_old_file(self):
  target=public_file('covers/demo.jpg',self.state);target.parent.mkdir(parents=True);target.write_bytes(b'old')
  with self.assertRaises(ValueError):cache_one(self.item(),self.state,Transport(b'wrong'))
  self.assertEqual(target.read_bytes(),b'old');self.assertFalse(target.with_suffix('.jpg.partial').exists())
 def test_cache_refuses_external_hosts_and_unsafe_identity(self):
  for key,value in [('url','https://example.com/a.jpg'),('url','https://someone:secret@motiongit.com/a.jpg'),('slug','../private')]:
   item=self.item();item[key]=value
   with self.assertRaises(ValueError):cache_one(item,self.state,Transport(b'valid'))
 def test_path_traversal_and_private_public_confusion(self):
  for value in ['../private','/tmp/private','a//b']:
   with self.assertRaises(ValueError):private_file(value,self.state)
  with self.assertRaises(ValueError):public_file('.motiongit-library/packages/secret.motion',self.state)
 def test_cache_symlink_target_is_not_overwritten(self):
  target=public_file('covers/demo.jpg',self.state);target.parent.mkdir(parents=True);outside=self.state/'safe.txt';outside.write_bytes(b'keep');target.symlink_to(outside)
  with self.assertRaises(ValueError):cache_one(self.item(),self.state,Transport(b'valid'))
  self.assertEqual(outside.read_bytes(),b'keep')
 def test_checker_finds_private_values_without_echoing(self):
  root=self.state/'repo';(root/'skills/rico-short-video').mkdir(parents=True);(root/'skills/rico-short-video/SKILL.md').write_text('---\nname: rico-short-video\n---\n')
  (root/'leak.txt').write_text('/'+'Users/'+'someone/private.txt\n'+'ghp_'+'x'*30)
  r=checker.check(root);kinds={x['kind'] for x in r['issues']}
  self.assertIn('private_local_path',kinds);self.assertIn('credential_value',kinds);self.assertNotIn('x'*30,json.dumps(r))
 def gallery(self):
  spec=importlib.util.spec_from_file_location('rico_public_gallery',ROOT/'skills/rico-short-video/scripts/motiongit/serve_gallery.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
 def test_gallery_uses_validated_cache_and_refuses_symlink_escape(self):
  with mock.patch.dict(os.environ,{'RICO_SHORT_VIDEO_DATA_HOME':str(self.state)}):
   initialize(self.state);item=self.item();cache_one(item,self.state,Transport(b'valid'))
   module=self.gallery();html=self.state/'gallery.html';html.write_text('<img src="'+item['url']+'">');sources=self.state/'sources.json';sources.write_text(json.dumps({'assets':[item]}));module.PATHS['gallery']=html;module.PATHS['preview_sources']=sources
   self.assertIn(b'/covers/demo.jpg',module.render_gallery());self.assertNotIn(item['url'].encode(),module.render_gallery())
   outside=self.state/'private';outside.mkdir();(outside/'key.txt').write_text('not served');(self.state/'public-media/licenses').rmdir();(self.state/'public-media/licenses').symlink_to(outside,target_is_directory=True)
   self.assertIsNone(module.resolve_target('/licenses/key.txt'));self.assertIsNone(module.resolve_target('/../profile.json'))
if __name__=='__main__':unittest.main()
