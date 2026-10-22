import base64
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'),'Node.js is needed for MG geometry checks')
class MGGeometry(unittest.TestCase):
    def test_portrait_landscape_framing_and_distant_parallax(self):
        source=(ROOT/'skills/rico-short-video/assets/mg-shared/geometry.js').read_bytes()
        uri='data:text/javascript;base64,'+base64.b64encode(source).decode()
        script='''import assert from 'node:assert/strict';
import {frameReadingRect,projectPoint,backgroundView} from %s;
for (const canvas of [{width:1080,height:1920},{width:1920,height:1080}]) {
 const viewport={x:70,y:150,width:canvas.width-140,height:canvas.height-300};
 const rect={x:-300,y:220,width:820,height:410};
 const camera=frameReadingRect(viewport,rect,{padding:.1});
 const center=projectPoint(canvas,camera,{x:rect.x+rect.width/2,y:rect.y+rect.height/2});
 assert.ok(Math.abs(center.x-(viewport.x+viewport.width/2))<1e-7);
 assert.ok(Math.abs(center.y-(viewport.y+viewport.height/2))<1e-7);
 for (const point of [{x:rect.x,y:rect.y},{x:rect.x+rect.width,y:rect.y+rect.height}]) {
  const p=projectPoint(canvas,camera,point);
  assert.ok(p.x>=viewport.x && p.x<=viewport.x+viewport.width);
  assert.ok(p.y>=viewport.y && p.y<=viewport.y+viewport.height);
 }
 const pose={scale:4,focusX:200,focusY:300,rx:20,rz:-12,perspective:2400};
 const distant=backgroundView(canvas,pose);
 assert.ok(distant.dotScale>1 && distant.dotScale<pose.scale);
 assert.ok(distant.haloScale>1 && distant.haloScale<distant.dotScale);
 const foreground=projectPoint(canvas,pose,{x:canvas.width/2,y:canvas.height/2});
 assert.ok(Math.abs(distant.dotX)<Math.abs(foreground.x-canvas.width/2));
 assert.ok(Math.abs(distant.haloX)<Math.abs(distant.dotX));
 assert.deepEqual(backgroundView(canvas,pose,{follow:false}),{dotScale:1,dotX:0,dotY:0,haloScale:1,haloX:0,haloY:0});
 assert.throws(()=>projectPoint(canvas,{}, {x:0,y:0,z:2500}),RangeError);
}
console.log('aspect framing and weaker camera-linked parallax passed');
''' % repr(uri)
        result=subprocess.run(['node','--input-type=module','-e',script],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':
    unittest.main()
