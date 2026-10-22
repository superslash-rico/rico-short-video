#!/usr/bin/env python3
"""Resolve pinned, study-only MG references into the user's external cache."""
import argparse,hashlib,json,os,sys,tempfile
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def resolve(args):
    manifest=json.loads((ROOT/'references/data/mg-reference-index.json').read_text())
    requested=set(args.ids.split(',')) if args.ids else None
    entries=[x for x in manifest['resources'] if requested is None or x['id'] in requested]
    if requested and requested-{x['id'] for x in entries}:raise ValueError('Unknown reference id')
    home=Path(args.data_root or os.environ.get('RICO_SHORT_VIDEO_DATA_HOME') or Path.home()/'.local/share/rico-short-video').expanduser().resolve()
    if home==ROOT or home.is_relative_to(ROOT):raise ValueError('Reference cache must be outside installed skill')
    cache=home/'mg-reference-cache'/manifest['source_commit']
    source=Path(args.source_dir).expanduser().resolve() if args.source_dir else None
    result=[]
    for entry in entries:
        rel=Path(entry['source_relative_path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe reference path')
        target=cache/rel
        if target.is_symlink() or not target.resolve().is_relative_to(cache.resolve()):raise ValueError('Unsafe cache path')
        ok=target.is_file() and target.stat().st_size==entry['bytes'] and digest(target)==entry['sha256']
        if not ok and (source or args.download):
            target.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as f:
                temporary=Path(f.name)
                try:
                    if source:
                        src=source/rel
                        if not src.resolve().is_relative_to(source):raise ValueError('Source escapes package')
                        if not src.is_file() or src.stat().st_size!=entry['bytes'] or digest(src)!=entry['sha256']:
                            raise ValueError('Source hash mismatch: '+entry['id'])
                        with src.open('rb') as inp:
                            for chunk in iter(lambda:inp.read(1024*1024),b''):f.write(chunk)
                    else:
                        with urlopen(entry['url'],timeout=60) as inp:
                            total=0
                            while chunk:=inp.read(1024*1024):
                                total+=len(chunk)
                                if total>entry['bytes']:raise ValueError('Reference exceeds pinned size')
                                f.write(chunk)
                    f.flush()
                    if temporary.stat().st_size!=entry['bytes'] or digest(temporary)!=entry['sha256']:
                        raise ValueError('Downloaded reference hash mismatch: '+entry['id'])
                    temporary.replace(target)
                finally:
                    temporary.unlink(missing_ok=True)
            ok=True
        result.append({'id':entry['id'],'status':'verified' if ok else 'missing_or_changed','path':str(target) if ok else None,
                       'url':entry['url'],'approved_scope':entry['approved_scope'],'use':entry['use']})
    return {'status':'verified' if all(x['status']=='verified' for x in result) else 'needs_references',
            'source_commit':manifest['source_commit'],'cache_root':str(cache),'resources':result,
            'scope':'Reference bytes only. Not permission to reuse sample people/audio or proof of native/visual acceptance.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-dir',help='Root of the downloaded long-video skill, containing SKILL.md')
    p.add_argument('--download',action='store_true',help='Fetch pinned public source URLs when missing')
    p.add_argument('--data-root',help='External state directory; never the installed skill')
    p.add_argument('--ids',help='Comma-separated resource IDs; omit for all')
    args=p.parse_args()
    try:
        r=resolve(args);print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['status']=='verified' else 2
    except (OSError,ValueError) as e:
        print(json.dumps({'status':'error','error':str(e)},ensure_ascii=False));return 1

if __name__=='__main__':sys.exit(main())
