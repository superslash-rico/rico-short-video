#!/usr/bin/env python3
"""Explicitly cache checksum-bound official public previews; no cookies or keys."""
import argparse,json,re,shutil,urllib.parse,urllib.request
from pathlib import Path
from paths import locations,public_file,digest
from setup_local import initialize
HOSTS={'motiongit.com','media.openaicut.com'}
class OfficialOnly(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,request,fp,code,msg,headers,newurl):
  parsed=urllib.parse.urlparse(newurl)
  if parsed.scheme!='https' or parsed.hostname not in HOSTS:raise ValueError('Redirect leaves official HTTPS hosts')
  return super().redirect_request(request,fp,code,msg,headers,newurl)
def cache_one(item,data_root,opener=None):
 parsed=urllib.parse.urlparse(item['url']);slug=item['slug'];kind=item['kind']
 if parsed.scheme!='https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:raise ValueError('Not an official credential-free HTTPS URL')
 if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',slug) or kind not in ('cover','card','full'):raise ValueError('Unsafe public media identity')
 relative=('covers/' if kind=='cover' else 'previews/')+slug+('.jpg' if kind=='cover' else '-'+kind+'.mp4')
 target=public_file(relative,data_root);target.parent.mkdir(parents=True,exist_ok=True)
 if target.is_symlink():raise ValueError('Cache target cannot be a symlink')
 if target.is_file() and target.stat().st_size==item['bytes'] and digest(target)==item['sha256']:return {'path':relative,'bytes':item['bytes'],'sha256':item['sha256'],'reused':True}
 temporary=target.with_suffix(target.suffix+'.partial')
 if temporary.exists() or temporary.is_symlink():raise ValueError('Partial cache exists; inspect before retrying')
 transport=opener or urllib.request.build_opener(OfficialOnly())
 try:
  with transport.open(item['url'],timeout=45) as source,temporary.open('xb') as output:
   remaining=item['bytes']+1
   while remaining:
    chunk=source.read(min(1024*1024,remaining))
    if not chunk:break
    output.write(chunk);remaining-=len(chunk)
  if temporary.stat().st_size!=item['bytes'] or digest(temporary)!=item['sha256']:raise ValueError('Official URL bytes changed; old cache retained')
  temporary.chmod(0o600);temporary.replace(target)
 finally:
  if temporary.exists():temporary.unlink()
 return {'path':relative,'bytes':item['bytes'],'sha256':item['sha256'],'reused':False}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--kind',choices=['cover','card','full','all'],default='cover');parser.add_argument('--download',action='store_true');parser.add_argument('--list',action='store_true');parser.add_argument('--data-root');a=parser.parse_args();p=locations(a.data_root);items=json.loads(p['preview_sources'].read_text())['assets'];items=[x for x in items if a.kind=='all' or x['kind']==a.kind]
 if not a.download:print(json.dumps({'kind':a.kind,'files':len(items),'bytes':sum(x['bytes'] for x in items),'downloaded':False},ensure_ascii=False));raise SystemExit(0)
 initialize(a.data_root);journal=json.loads(p['asset_index'].read_text());by_path={x['path']:x for x in journal.get('assets',[])};failures=[]
 for item in items:
  try:
   value=cache_one(item,a.data_root);by_path[value['path']]=value
   temp=p['asset_index'].with_suffix('.writing');temp.write_text(json.dumps({'schema_version':1,'assets':list(by_path.values())},ensure_ascii=False,indent=2)+'\n');temp.replace(p['asset_index'])
  except Exception as error:failures.append({'slug':item['slug'],'error':str(error)})
 print(json.dumps({'processed':len(items),'cached':len(by_path),'failures':failures},ensure_ascii=False,indent=2));raise SystemExit(1 if failures else 0)
