#!/usr/bin/env python3
"""Local private-package ingest/audit; never reads credentials or downloads packages."""
import argparse
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from paths import locations


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def ingest(root, paths):
    private = root / '.motiongit-library'
    private.mkdir(exist_ok=True)
    private.chmod(0o700)
    journal = private / 'acquisitions.json'
    data = json.loads(journal.read_text()) if journal.exists() else {'schema': 1, 'packages': []}
    added = []
    for source in paths:
        source = source.resolve(strict=True)
        with zipfile.ZipFile(source) as z:
            # Only the public first-read metadata is opened. Protected and personal entries stay intact.
            guide = json.loads(z.read('assistant/guide.json'))
        identity = guide['template']
        slug, version = str(identity['id']), str(identity['version'])
        if not all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', x) for x in (slug, version)):
            raise ValueError('Invalid public template id/version; nothing copied')
        sha = digest(source)
        existing = next((x for x in data['packages'] if x['sha256'] == sha), None)
        if existing:
            if not (root / existing['path']).is_file() or digest(root / existing['path']) != sha:
                raise ValueError('Existing journal entry has missing or altered bytes')
            continue
        folder = private / 'packages' / slug / version
        folder.mkdir(parents=True, exist_ok=True)
        for d in (folder, folder.parent, folder.parent.parent):
            d.chmod(0o700)
        target = folder / f'{slug}-{version}.personal.motion'
        if target.exists() and digest(target) != sha:
            target = folder / f'{slug}-{version}.{sha[:12]}.personal.motion'
        if not target.exists():
            temporary = target.with_suffix('.partial')
            shutil.copyfile(source, temporary)
            temporary.chmod(0o600)
            if digest(temporary) != sha:
                raise ValueError('Copy integrity mismatch')
            temporary.replace(target)
        target.chmod(0o600)
        record = {'template_slug': slug, 'version': version, 'name': identity.get('name'),
                  'path': str(target.relative_to(root)), 'bytes': target.stat().st_size,
                  'sha256': sha, 'acquired_at': datetime.now(timezone.utc).isoformat(),
                  'identity_status': 'public_self_description_only', 'signature_verified': False,
                  'source_method': 'official_browser_download'}
        data['packages'].append(record)
        save(journal, data)  # A completed package is checkpointed before the next import.
        added.append({'slug': slug, 'version': version, 'bytes': record['bytes']})
    return {'added': added, 'total_journal_packages': len(data['packages'])}


def audit(root):
    path = root / '.motiongit-library/acquisitions.json'
    journal = json.loads(path.read_text())
    errors, size = [], 0
    for item in journal['packages']:
        p = (root / item['path']).resolve()
        if not p.is_relative_to((root / '.motiongit-library').resolve()):
            errors.append({'path': item['path'], 'error': 'outside_private_library'})
            continue
        if not p.is_file():
            errors.append({'path': item['path'], 'error': 'missing'})
            continue
        size += p.stat().st_size
        if p.stat().st_size != item['bytes'] or digest(p) != item['sha256']:
            errors.append({'path': item['path'], 'error': 'integrity_mismatch'})
        if p.stat().st_mode & 0o077:
            errors.append({'path': item['path'], 'error': 'not_private'})
        if any(d.stat().st_mode & 0o077 for d in (p.parent, p.parent.parent, p.parent.parent.parent, root / '.motiongit-library')):
            errors.append({'path': item['path'], 'error': 'directory_not_private'})
    return {'packages': len(journal['packages']), 'bytes': size, 'errors': errors,
            'scope': 'local bytes and permissions only; no signature, runtime or visual approval implied'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root', type=Path, help='Global private state root; default from paths.py')
    p.add_argument('--project', type=Path, help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest='command', required=True)
    i = sub.add_parser('ingest')
    i.add_argument('packages', type=Path, nargs='+')
    sub.add_parser('audit')
    args = p.parse_args()
    root = (args.data_root or args.project or locations()['data_root']).resolve()
    if args.command == 'ingest':
        from setup_local import initialize
        initialize(root)
    result = ingest(root, args.packages) if args.command == 'ingest' else audit(root)
    print(json.dumps(result, ensure_ascii=False))
    if result.get('errors'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
