#!/usr/bin/env python3
"""Check the public tree without echoing suspected sensitive values."""
import ast,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','__pycache__','.artifacts','.venv'}
MEDIA={'.motion','.mov','.mp4','.mp3','.wav','.png','.jpg','.jpeg','.zip'}
PATTERNS={
 'private_local_path':re.compile('/'+r'(?:Users|Volumes|private/var/folders|var/folders)/[^\s<>"\']+'),
 'internal_document_url':re.compile(r'https?://[^/\s]+\.(?:feishu|larksuite)\.(?:cn|com)/(?:sheets|docx|wiki|base)/'),
 'credential_value':re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{24,}|Bearer\s+[A-Za-z0-9._~+/=-]{12,}|editor-boot-token[=]'),
 'quoted_secret':re.compile(r'["\'](?:apiKey|api_key|access_token|refresh_token|cookie)["\']\s*:\s*["\'][^"\'\n]{8,}["\']',re.I),
}
PRIVATE_FIELDS={'apiKeyId','recipientAccountId','local_package_sha256','private_package_path','verification_record','browserHandoff','draft_id','draftId','account_scope','historical_evidence_record'}
def json_issues(value,path):
 issues=[]
 if isinstance(value,dict):
  for key,v in value.items():
   if key in PRIVATE_FIELDS and v not in (None,False,'',[],{}):issues.append({'path':path,'kind':'private_account_field','field':key})
   issues+=json_issues(v,path)
 elif isinstance(value,list):
  for v in value:issues+=json_issues(v,path)
 return issues
def check(root=ROOT):
 root=Path(root).resolve();issues=[];files=[]
 for p in sorted(root.rglob('*')):
  rel=p.relative_to(root)
  if any(part in SKIP for part in rel.parts):continue
  if p.is_symlink():issues.append({'path':rel.as_posix(),'kind':'symlink'});continue
  if not p.is_file():continue
  files.append(p)
  if p.suffix.lower() in MEDIA:issues.append({'path':rel.as_posix(),'kind':'unapproved_binary'})
  if p.stat().st_size>2*1024*1024:issues.append({'path':rel.as_posix(),'kind':'unexpected_large_file'})
  try:text=p.read_text(encoding='utf-8')
  except UnicodeDecodeError:issues.append({'path':rel.as_posix(),'kind':'non_utf8'});continue
  for name,pattern in PATTERNS.items():
   if pattern.search(text):issues.append({'path':rel.as_posix(),'kind':name})
  if p.suffix=='.py':
   try:ast.parse(text,filename=rel.as_posix())
   except SyntaxError:issues.append({'path':rel.as_posix(),'kind':'python_syntax'})
  if p.suffix=='.json':
   try:issues+=json_issues(json.loads(text),rel.as_posix())
   except json.JSONDecodeError:issues.append({'path':rel.as_posix(),'kind':'json_syntax'})
  if p.suffix=='.md':
   for target in re.findall(r'\]\(([^)]+)\)',text):
    target=target.strip('<>')
    if ':' in target or target.startswith('#'):continue
    dest=(p.parent/target.split('#')[0]).resolve()
    if not dest.is_relative_to(root) or not dest.exists():issues.append({'path':rel.as_posix(),'kind':'broken_relative_link','target':target})
 skill=root/'skills/rico-short-video/SKILL.md'
 if not skill.is_file() or not skill.read_text().startswith('---\nname: rico-short-video\n'):issues.append({'kind':'skill_entry'})
 return {'status':'passed' if not issues else 'failed','files':len(files),'bytes':sum(p.stat().st_size for p in files),'issues':issues,'scope':'Automated checks supplement human review; not an absolute secret-free guarantee.'}
if __name__=='__main__':
 r=check();print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(0 if r['status']=='passed' else 1)
