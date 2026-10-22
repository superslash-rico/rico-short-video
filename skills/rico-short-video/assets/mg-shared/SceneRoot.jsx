import React from 'react';
import {useVideoConfig} from 'remotion';
import {resolveCamera,backgroundView} from './geometry.js';
import standard from './standard.json';

// Import the asset at the actual project canvas size and place it at (0,0).
// The final render surface is the only scene viewport. No middle-window mask.
export function FullCanvas({children,fontFamily=standard.visual.fontFamily}){
 const {width,height}=useVideoConfig();
 return <div style={{position:'absolute',inset:0,width,height,overflow:'visible',fontFamily}}>{children}</div>;
}
export function CameraWorld({camera,children}){
 const {width,height}=useVideoConfig(),c=resolveCamera({width,height},camera);
 return <div style={{position:'absolute',inset:0,overflow:'visible',perspective:c.perspective,perspectiveOrigin:`${c.centerX}px ${c.centerY}px`,transformStyle:'preserve-3d'}}>
  <div style={{position:'absolute',left:c.centerX-c.focusX,top:c.centerY-c.focusY,width,height,overflow:'visible',transformOrigin:`${c.focusX}px ${c.focusY}px 0`,transformStyle:'preserve-3d',transform:`scale3d(${c.scale},${c.scale},1) rotateX(${c.rx}deg) rotateZ(${c.rz}deg)`}}>{children}</div>
 </div>;
}
export function SharedBackdrop({camera,referenceScale=1,follow=true,showDots=true,showGlow=true,transparent=false,profile=standard.visual.background,patternId='shared-mg-background'}){
 const {width,height}=useVideoConfig(),p=profile;
 const v=backgroundView({width,height},camera,{referenceScale,follow}),unit=Math.min(width,height)/1080;
 const spacing=p.dotSpacing*unit,radius=p.dotRadius*unit,cx=width/2,cy=height/2,haloHeight=p.glowHeight*unit;
 if(transparent)return null;
 return <div style={{position:'absolute',inset:0,backgroundColor:p.base}}>
  <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{position:'absolute',inset:0}}>
   <defs>
    <pattern id={patternId+'-dots'} width={spacing} height={spacing} patternUnits="userSpaceOnUse"><circle cx={spacing/2} cy={spacing/2} r={radius} fill={p.dotColor} fillOpacity={p.dotOpacity}/></pattern>
    <radialGradient id={patternId+'-glow'}><stop offset="0" stopColor="#EBD9F3" stopOpacity={1}/><stop offset=".3" stopColor={p.glowColor} stopOpacity={.68}/><stop offset=".68" stopColor={p.glowColor} stopOpacity={.22}/><stop offset="1" stopColor={p.glowColor} stopOpacity={0}/></radialGradient>
   </defs>
   {showGlow&&<g transform={`translate(${v.haloX} ${v.haloY}) translate(${cx} ${cy}) scale(${v.haloScale}) translate(${-cx} ${-cy})`}><ellipse cx={cx} cy={cy} rx={width*.78} ry={haloHeight} fill={`url(#${patternId}-glow)`} opacity={p.glowOpacity*.55}/><ellipse cx={cx} cy={cy} rx={width*.73} ry={haloHeight*.48} fill={`url(#${patternId}-glow)`} opacity={p.glowOpacity}/></g>}
   {showDots&&<g transform={`translate(${v.dotX} ${v.dotY}) translate(${cx} ${cy}) scale(${v.dotScale}) translate(${-cx} ${-cy})`}><rect x={-width} y={-height} width={width*3} height={height*3} fill={`url(#${patternId}-dots)`}/></g>}
  </svg>
 </div>;
}
