import assert from 'node:assert/strict';
import {visibleDotGrid,backgroundResourceId} from '../assets/mg-shared/geometry.js';

let cases=0;
for(const [width,height] of [[1080,1920],[1920,1080],[2160,3840]]){
 for(const scale of [.55,.94,1,1.24,1.45])for(const [dotX,dotY] of [[0,0],[250,-400],[-500,700]]){
  const canvas={width,height},v={dotScale:scale,dotX,dotY},spacing=42*Math.min(width,height)/1080;
  const points=visibleDotGrid(canvas,v,spacing),keys=points.map(p=>p.key);
  assert.equal(new Set(keys).size,points.length);
  const xs=points.map(p=>dotX+width/2+(p.x-width/2)*scale);
  const ys=points.map(p=>dotY+height/2+(p.y-height/2)*scale);
  assert.ok(Math.min(...xs)<0&&Math.max(...xs)>width,'horizontal coverage');
  assert.ok(Math.min(...ys)<0&&Math.max(...ys)>height,'vertical coverage');
  for(const p of points.slice(0,6))assert.ok(Math.abs(p.x/spacing-.5-Math.round(p.x/spacing-.5))<1e-8,'stable grid phase');
  assert.deepEqual(points,visibleDotGrid(canvas,v,spacing),'deterministic seeking');cases++;
 }
}
assert.notEqual(backgroundResourceId('instance-a'),backgroundResourceId('instance-b'));
assert.equal(backgroundResourceId('instance-a'),backgroundResourceId('instance-a'));
for(const key of [undefined,'','has whitespace'])assert.throws(()=>backgroundResourceId(key));
assert.throws(()=>visibleDotGrid({width:1080,height:1920},{dotScale:1,dotX:0,dotY:0},0));
console.log(JSON.stringify({status:'passed',viewportCases:cases,scope:'coverage, deterministic grid and resource-key validation; native rendering checked separately'}));
