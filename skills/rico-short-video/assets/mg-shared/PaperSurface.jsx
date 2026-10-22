// Material study adapted from the user's course-long-video-editing v1.3.0
// project-record derivative of video-shotcraft 43bd349a136651865ecfa6ea1cf012f6e957d304 (Apache-2.0).
// This is a content-bearing paper object, not a generic enclosing scene card.
import React from 'react';
import standard from './standard.json';

export function PaperSurface({x,y,z=0,width,height,rx=0,ry=0,rz=0,elevation=8,material=standard.visual.paper,shade=0,children}){
 shade=Math.min(1,Math.max(0,Number.isFinite(shade)?shade:0));
 const tone=(color,a)=>{const h=color.slice(1),b='0C0A14';return '#'+[0,2,4].map(i=>Math.round(parseInt(b.slice(i,i+2),16)+(parseInt(h.slice(i,i+2),16)-parseInt(b.slice(i,i+2),16))*(1-a)).toString(16).padStart(2,'0')).join('');};
 const p={...material,edge:tone(material.edge,shade),thickness:tone(material.thickness,shade)};
 const contact=.12/(1+elevation/24),ambient=.08+Math.min(elevation,64)/64*.22;
 return <div style={{position:'absolute',left:x,top:y,width,height,overflow:'visible',transformStyle:'preserve-3d',transform:`translateZ(${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg)`}}>
  <div style={{position:'absolute',inset:0,borderRadius:p.radius,background:p.thickness,transform:`translateZ(${-p.thicknessPx}px)`,backfaceVisibility:'hidden'}}/>
  <div style={{position:'absolute',inset:0,boxSizing:'border-box',padding:32,borderRadius:p.radius,background:`linear-gradient(150deg,${p.surface},${p.secondary})`,color:p.ink,border:`${p.edgeWidthPx}px solid ${p.edge}`,boxShadow:`inset 0 1px 0 #ffffffcc,0 ${.5+elevation*.06}px ${1+elevation*.18}px rgba(38,19,46,${contact}),0 ${elevation*.55}px ${elevation*1.3}px rgba(38,19,46,${ambient})`,backfaceVisibility:'hidden',overflow:'visible',display:'flex',flexDirection:'column',gap:20}}>{children}{shade>0&&<div style={{position:"absolute",inset:0,borderRadius:p.radius,backgroundColor:"#0C0A14",opacity:Math.min(1,Math.max(0,shade)),pointerEvents:"none"}}/>}</div>
 </div>;
}
