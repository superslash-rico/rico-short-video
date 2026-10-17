#!/usr/bin/env python3
"""Create empty local state without overwriting existing user configuration."""
import argparse,json,os
from pathlib import Path
from paths import locations

def create_json_once(path,value):
 try:
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 except FileExistsError:return False
 with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 return True

def initialize(data_root=None):
 p=locations(data_root)
 for folder in [p['data_root'],p['private_library'],p['private_library']/'packages',p['public_media'],p['public_media']/'covers',p['public_media']/'previews',p['public_media']/'licenses',p['history']]:
  if folder.is_symlink():raise ValueError('Setup refuses a symlinked state directory')
  folder.mkdir(parents=True,exist_ok=True,mode=0o700)
 created=[]
 if create_json_once(p['profile'],{'schema_version':1,'author_name':'Rico','course_catalog_path':None,'verified_membership_benefits':[],'note':'Fill your own confirmed information. This is not account authorization.'}):created.append('profile.json')
 if create_json_once(p['private_library']/'acquisitions.json',{'schema':1,'packages':[]}):created.append('private package journal')
 if create_json_once(p['asset_index'],{'schema_version':1,'assets':[]}):created.append('public preview journal')
 return {'status':'initialized','created':created,'data_root':str(p['data_root']),'account_authorization':'not_performed','template_downloads':'not_performed'}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-root');args=parser.parse_args();print(json.dumps(initialize(args.data_root),ensure_ascii=False,indent=2))
