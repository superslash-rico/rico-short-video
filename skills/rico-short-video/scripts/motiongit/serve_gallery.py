#!/usr/bin/env python3
"""Serve public previews on loopback; never expose personal state or templates."""
import argparse,functools,json,mimetypes,re,sys,urllib.parse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from paths import locations,public_file,digest
PATHS=locations();ROOT=PATHS['public_media']
@functools.lru_cache(maxsize=1)
def render_gallery():
 text=PATHS['gallery'].read_text()
 source=json.loads(PATHS['preview_sources'].read_text())['assets']
 for item in source:
  name=item['slug']+('.jpg' if item['kind']=='cover' else '-'+item['kind']+'.mp4')
  rel=('covers/' if item['kind']=='cover' else 'previews/')+name
  try:p=public_file(rel)
  except ValueError:continue
  if p.is_file() and not p.is_symlink() and p.stat().st_size==item['bytes'] and digest(p)==item['sha256']:
   text=text.replace(item['url'],'/'+rel)
 return text.encode('utf-8')
def resolve_target(route):
 if ROOT.is_symlink():return None
 base=ROOT.resolve();target=(ROOT/route.lstrip('/')).resolve()
 allowed=[(ROOT/k).resolve() for k in ['covers','previews','licenses']]
 if not target.is_relative_to(base) or not any(folder.is_relative_to(base) and target.is_relative_to(folder) for folder in allowed) or not target.is_file():return None
 return target
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):self.deliver(True)
 def do_HEAD(self):self.deliver(False)
 def deliver(self,body):
  route=urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
  if route in ['/','/gallery','/gallery.html']:
   data=render_gallery();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','private, max-age=0');self.end_headers()
   if body:self.wfile.write(data)
   return
  target=resolve_target(route)
  if target is None:self.send_error(404);return
  size=target.stat().st_size;start=0;end=size-1;value=self.headers.get('Range')
  if value:
   match=re.fullmatch(r'bytes=(\d+)-(\d*)',value)
   if not match:self.send_error(416);return
   start=int(match[1]);end=min(int(match[2]),end) if match[2] else end
   if start>end or start>=size:self.send_error(416);return
  self.send_response(206 if value else 200);self.send_header('Content-Type',mimetypes.guess_type(target.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
  if value:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
  self.end_headers()
  if body:
   try:
    with target.open('rb') as f:
     f.seek(start);remaining=end-start+1
     while remaining:
      chunk=f.read(min(256*1024,remaining))
      if not chunk:break
      self.wfile.write(chunk);remaining-=len(chunk)
   except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,*args):pass
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=0);a=parser.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);print(f'http://127.0.0.1:{server.server_port}/',flush=True);server.serve_forever()
