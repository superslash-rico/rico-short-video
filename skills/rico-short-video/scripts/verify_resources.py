#!/usr/bin/env python3
"""Check public package references; optionally inspect only this user's own cache."""
import argparse,json,re
from pathlib import Path
from paths import SKILL_ROOT,locations,private_file,public_file,digest

def verify(check_media=False,check_private=False,data_root=None):
 p=locations(data_root);errors=[];status='passed';counts={'templates':len(json.loads(p['catalog'].read_text())['entries'])}
 for doc in [SKILL_ROOT/'SKILL.md',*SKILL_ROOT.glob('references/**/*.md')]:
  for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
   if ':' in link or link.startswith('#'):continue
   target=(doc.parent/link.strip('<>').split('#')[0]).resolve()
   if not target.is_relative_to(SKILL_ROOT) or not target.exists():errors.append({'source':doc.relative_to(SKILL_ROOT).as_posix(),'missing':link})
 if any(SKILL_ROOT.rglob('*.motion')):errors.append({'error':'Personal template packages must not be distributed'})
 counts['private_authorization']='not_checked'
 if check_private:
  journal=p['private_library']/'acquisitions.json'
  packages=json.loads(journal.read_text())['packages'] if journal.is_file() else []
  counts['local_packages']=len(packages)
  if not packages:status='needs_setup';errors.append({'private_cache':'No personal packages registered; obtain your own official templates'})
  for entry in packages:
   target=private_file(entry['path'],data_root)
   if not target.is_file() or target.stat().st_size!=entry['bytes'] or digest(target)!=entry['sha256']:errors.append({'invalid_local_package':entry['path']})
  counts['private_authorization']='not_verified_by_hash_check'
 if check_media:
  media=json.loads(p['asset_index'].read_text()).get('assets',[]) if p['asset_index'].is_file() else []
  counts['cached_media']=len(media)
  if not media:status='needs_optional_media_cache';errors.append({'media_cache':'No optional preview media cached'})
  for item in media:
   target=public_file(item['path'],data_root)
   if not target.is_file() or digest(target)!=item['sha256']:errors.append({'invalid_cached_media':item['path']})
 if errors and status=='passed':status='failed'
 return {'status':status,'counts':counts,'errors':errors,'scope':'Structure and optional local bytes only; not account, signature, render or visual approval'}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check-media',action='store_true');parser.add_argument('--check-private',action='store_true');parser.add_argument('--data-root');a=parser.parse_args();r=verify(a.check_media,a.check_private,a.data_root);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['status']=='passed' else 2)
