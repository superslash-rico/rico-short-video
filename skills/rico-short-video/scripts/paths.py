#!/usr/bin/env python3
"""Portable public-edition paths; all personal state stays on this machine."""
import argparse,hashlib,json,os
from pathlib import Path,PurePosixPath
SKILL_ROOT=Path(__file__).resolve().parents[1]
def locations(data_root=None):
 state=Path(data_root or os.environ.get('RICO_SHORT_VIDEO_DATA_HOME') or Path.home()/'.local/share/rico-short-video').expanduser().resolve()
 return {'skill_root':SKILL_ROOT,'data_root':state,'private_library':state/'.motiongit-library','history':state/'history','public_media':state/'public-media','profile':state/'profile.json','catalog':SKILL_ROOT/'references/data/motiongit-catalog.json','index':SKILL_ROOT/'references/data/motiongit-index.json','experience':SKILL_ROOT/'references/data/motiongit-experience.json','asset_index':state/'public-assets.json','preview_sources':SKILL_ROOT/'references/data/preview-sources.json','gallery':SKILL_ROOT/'assets/motiongit/gallery.html'}
def relative_path(value):
 if not isinstance(value,str) or not value or '\\' in value:raise ValueError('Expected a relative resource path')
 p=PurePosixPath(value)
 if p.is_absolute() or p.as_posix()!=value or any(x in ('.','..') for x in p.parts):raise ValueError('Unsafe resource path')
 return p
def public_reference(value):
 p=relative_path(value)
 if p.parts[:2]==('assets','motiongit'):p=PurePosixPath(*p.parts[2:])
 elif p.parts[0]=='.motiongit-library':p=PurePosixPath(*p.parts[1:])
 if not p.parts or p.parts[0] not in ('covers','previews','licenses'):raise ValueError('Not a public-media reference')
 return p.as_posix()
def public_file(value,data_root=None):
 root=locations(data_root)['public_media'];p=root/public_reference(value)
 if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Public path escapes cache')
 return p
def private_file(value,data_root=None):
 p=relative_path(value)
 if p.parts[0]=='.motiongit-library':p=PurePosixPath(*p.parts[1:])
 root=locations(data_root)['private_library'];target=root.joinpath(*p.parts)
 if not target.resolve().is_relative_to(root.resolve()):raise ValueError('Private path escapes library')
 return target
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--get',choices=list(locations()));parser.add_argument('--data-root');a=parser.parse_args();p=locations(a.data_root)
 print(str(p[a.get]) if a.get else json.dumps({k:str(v) for k,v in p.items()},ensure_ascii=False,indent=2))
