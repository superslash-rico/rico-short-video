// Full-canvas geometry. A reading frame guides composition; it never clips pixels.
const positive=(n,key)=>{if(!Number.isFinite(n)||n<=0)throw new RangeError(key);return n;};
export function frameReadingRect(viewport,rect,{padding=.08}={}){
  positive(viewport.width,'viewport.width');positive(viewport.height,'viewport.height');
  positive(rect.width,'rect.width');positive(rect.height,'rect.height');
  if(padding<0||padding>=.5)throw new RangeError('padding');
  return {focusX:rect.x+rect.width/2,focusY:rect.y+rect.height/2,
    centerX:viewport.x+viewport.width/2,centerY:viewport.y+viewport.height/2,
    scale:Math.min(viewport.width*(1-2*padding)/rect.width,viewport.height*(1-2*padding)/rect.height),
    rx:0,rz:0,perspective:2400};
}
export function resolveCamera(canvas,pose={}){
  positive(canvas.width,'canvas.width');positive(canvas.height,'canvas.height');
  const c={focusX:canvas.width/2,focusY:canvas.height/2,centerX:canvas.width/2,centerY:canvas.height/2,
    scale:1,rx:0,rz:0,perspective:2400,...pose};
  for(const [k,v] of Object.entries(c))if(!Number.isFinite(v))throw new RangeError(k);
  positive(c.scale,'scale');positive(c.perspective,'perspective');return c;
}
export function projectPoint(canvas,pose,point){
  const c=resolveCamera(canvas,pose),z=point.z??0;
  const x=point.x-c.focusX,y=point.y-c.focusY,a=c.rz*Math.PI/180,b=c.rx*Math.PI/180;
  const X=x*Math.cos(a)-y*Math.sin(a),Y=x*Math.sin(a)+y*Math.cos(a);
  const yy=Y*Math.cos(b)-z*Math.sin(b),zz=Y*Math.sin(b)+z*Math.cos(b);
  if(c.perspective-zz<=0)throw new RangeError('point behind camera plane');
  const k=c.perspective/(c.perspective-zz);
  return {x:c.centerX+X*c.scale*k,y:c.centerY+yy*c.scale*k,z:zz};
}
export function backgroundView(canvas,pose,{referenceScale=1,follow=true}={}){
  const c=resolveCamera(canvas,pose);positive(referenceScale,'referenceScale');
  if(!follow)return {dotScale:1,dotX:0,dotY:0,haloScale:1,haloX:0,haloY:0};
  const centre=projectPoint(canvas,c,{x:canvas.width/2,y:canvas.height/2,z:0});
  const dotScale=1+.45*Math.tanh(Math.log(c.scale/referenceScale)*.2);
  const dotX=(centre.x-canvas.width/2)*.055,dotY=(centre.y-canvas.height/2)*.055;
  return {dotScale,dotX,dotY,haloScale:1+(dotScale-1)*.25,haloX:dotX*.08,haloY:dotY*.08};
}

// Stable coordinates for explicit dots; include the inverse-transformed viewport.
// This avoids SVG pattern URL references and keeps coverage during parallax.
export function visibleDotGrid(canvas,view,spacing){
  positive(canvas.width,'canvas.width');positive(canvas.height,'canvas.height');
  positive(spacing,'dot spacing');positive(view.dotScale,'dot scale');
  if(!Number.isFinite(view.dotX)||!Number.isFinite(view.dotY))throw new RangeError('dot translation');
  const cx=canvas.width/2,cy=canvas.height/2,s=view.dotScale;
  const x0=cx+(-view.dotX-cx)/s,x1=cx+(canvas.width-view.dotX-cx)/s;
  const y0=cy+(-view.dotY-cy)/s,y1=cy+(canvas.height-view.dotY-cy)/s;
  const i0=Math.floor(x0/spacing-.5)-1,i1=Math.ceil(x1/spacing-.5)+1;
  const j0=Math.floor(y0/spacing-.5)-1,j1=Math.ceil(y1/spacing-.5)+1;
  if((i1-i0+1)*(j1-j0+1)>20000)throw new RangeError('dot grid too dense for this component');
  const points=[];
  for(let j=j0;j<=j1;j++)for(let i=i0;i<=i1;i++)points.push({x:(i+.5)*spacing,y:(j+.5)*spacing,key:`${i}:${j}`});
  return points;
}

// A stable per-instance key is supplied by the entry, never by wall clock/random.
export function backgroundResourceId(resourceKey,role='glow'){
  if(typeof resourceKey!=='string'||!resourceKey||!/^[A-Za-z0-9_.-]+$/.test(resourceKey))throw new TypeError('SharedBackdrop requires a stable unique resourceKey for each instance');
  if(typeof role!=='string'||!/^[A-Za-z0-9_.-]+$/.test(role))throw new TypeError('Invalid SVG resource role');
  return `rico-bg-${resourceKey}-${role}`;
}
