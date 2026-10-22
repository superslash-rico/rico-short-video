// MG-only study from the accepted paired benchmark; no presenter or audio.
import React from 'react';
import {useCurrentFrame,useVideoConfig} from 'remotion';
import {FullCanvas,CameraWorld,SharedBackdrop} from './SceneRoot.jsx';
import {PaperSurface} from './PaperSurface.jsx';
import {projectPoint} from './geometry.js';
import standard from './standard.json';

const clamp=(v)=>Math.min(1,Math.max(0,v));
const smooth=(v)=>{v=clamp(v);return v*v*v*(v*(v*6-15)+10);};
const ramp=(t,a,b)=>smooth((t-a)/(b-a));
const mix=(a,b,p)=>a+(b-a)*p;
const blend=(a,b,p)=>Object.fromEntries(Object.keys(a).map(k=>[k,mix(a[k],b[k],p)]));

// The two adapters share the same named objects and choreography, not a scaled frame.
function layout(portrait){
 return portrait?{
  board:{x:0,y:0,w:1100,h:1530},
  self:{x:60,y:185,w:980,h:370},
  goal:{x:60,y:635,w:980,h:155},
  resource:{x:60,y:825,w:470,h:395},
  colleague:{x:570,y:825,w:470,h:395},
  result:{x:60,y:1255,w:980,h:200}
 }:{
  board:{x:0,y:0,w:1690,h:1020},
  self:{x:65,y:180,w:520,h:725},
  goal:{x:660,y:180,w:965,h:160},
  resource:{x:660,y:385,w:465,h:340},
  colleague:{x:1160,y:385,w:465,h:340},
  result:{x:660,y:770,w:965,h:155}
 };
}
function aim(canvas,rect,z,s,rx,rz,cx,cy){
 const c={focusX:rect.x+rect.w/2,focusY:rect.y+rect.h/2,centerX:cx,centerY:cy,scale:s,rx,rz,perspective:2400};
 const q=projectPoint(canvas,c,{x:c.focusX,y:c.focusY,z});
 c.centerX+=cx-q.x;c.centerY+=cy-q.y;return c;
}
function poseAt(t,portrait,L,lift){
 const canvas=portrait?{width:1080,height:1920}:{width:1920,height:1080};
 const cx=portrait?540:880,cy=portrait?680:550;
 const overall=aim(canvas,L.board,0,portrait?.57:.66,portrait?44:43,portrait?-13:-13,cx,cy);
 const self=aim(canvas,L.self,12,portrait?1.02:1.04,13,-4,portrait?550:770,portrait?660:520);
 const res={...L.resource,x:L.resource.x-lift.resource*46,y:L.resource.y-lift.resource*18};
 const col={...L.colleague,x:L.colleague.x+lift.colleague*38,y:L.colleague.y-lift.colleague*22};
 const resource=aim(canvas,res,12+lift.resource*170,portrait?1.68:2.05,16,-5,portrait?550:820,portrait?650:500);
 const colleague=aim(canvas,col,12+lift.colleague*200,portrait?1.68:2.05,14,-4,portrait?550:820,portrait?650:500);
 const result=aim(canvas,L.board,0,portrait?.59:.69,portrait?38:36,portrait?-10:-10,cx,portrait?700:565);
 let c=overall;
 if(t>=1.65)c=blend(overall,self,ramp(t,1.65,2.13));
 if(t>=3.06)c=blend(self,overall,ramp(t,3.06,3.56));
 if(t>=4.05)c=blend(overall,resource,ramp(t,4.05,4.57));
 if(t>=6.25)c=blend(resource,colleague,ramp(t,6.25,6.73));
 if(t>=8.02)c=blend(colleague,result,ramp(t,8.02,8.61));
 return {camera:c,referenceScale:overall.scale};
}
const bodyStyle={fontWeight:500,lineHeight:1.36,whiteSpace:'normal',overflowWrap:'break-word',flexShrink:0};
function Tick({progress=1,color,size=85}){return <svg width={size} height={size} viewBox="0 0 100 100" style={{flexShrink:0}}><circle cx="50" cy="50" r="44" fill="none" stroke={color} strokeOpacity=".2" strokeWidth="4"/><path d="M25 51 L43 68 L77 31" fill="none" stroke={color} strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1-clamp(progress)}/></svg>;}
function Sheet({r,z=12,rx=0,rz=0,material,children,elevation=8,opacity=1}){return <div style={{transformStyle:'preserve-3d',overflow:'visible'}}><PaperSurface x={r.x} y={r.y} z={z} width={r.w} height={r.h} rx={rx} rz={rz} elevation={elevation} material={material} shade={1-opacity}>{children}</PaperSurface></div>;}
function Packet({r,z,shift=0,caption,detail,p,active,opacity=1}){
 return <Sheet r={{...r,x:r.x+shift}} z={z} material={{...standard.visual.paper,accent:p.accentColor}} elevation={z/4} opacity={opacity}>
  <div style={{...bodyStyle,color:p.inkColor,fontSize:Math.min(72,Math.floor((r.w-64)/(Math.min(caption.length,8)+.3))),fontWeight:700,letterSpacing:-1}}>{caption}</div>
  <div style={{...bodyStyle,color:p.inkColor,fontSize:detail.length>10?35:43,maxWidth:370}}>{detail}</div>
  <div style={{display:'flex',alignItems:'center',gap:16,marginTop:'auto',opacity:active,color:p.accentColor,fontSize:35,fontWeight:600}}><Tick size={48} color={p.accentColor} progress={active}/>接入目标</div>
 </Sheet>;
}

export default function TaskModels({item}){
 const frame=useCurrentFrame();const {fps,width,height}=useVideoConfig();const t=frame/fps;
 const p=item.props,portrait=height>width,L=layout(portrait);
 const assemble=ramp(t,7.93,8.62);
 const lift={resource:ramp(t,4.13,4.78)*(1-assemble),colleague:ramp(t,6.29,6.92)*(1-assemble)};
 const {camera,referenceScale}=poseAt(t,portrait,L,lift);
 const paper={...standard.visual.paper,ink:p.inkColor,accent:p.accentColor};
 const selfFocus=ramp(t,1.65,2.13)*(1-ramp(t,3.06,3.56));
 const resFocus=ramp(t,4.05,4.57)*(1-ramp(t,6.25,6.73));
 const colFocus=ramp(t,6.25,6.73)*(1-ramp(t,8.02,8.61));
 const detailFocus=Math.max(selfFocus,resFocus,colFocus);
 const nonfocus=1-.94*detailFocus;
 const done=ramp(t,1.93,2.38),resDone=ramp(t,4.79,5.25),colDone=ramp(t,6.91,7.4);
 const boardIntro=ramp(t,.27,.6);
 const chrome=clamp((1-ramp(t,1.65,1.88))+ramp(t,8.36,8.62));
 const resultDone=ramp(t,8.42,8.9);
 return <FullCanvas fontFamily={p.fontFamily}>
  <SharedBackdrop camera={camera} referenceScale={referenceScale} follow={p.parallax} transparent={p.transparentBackground} profile={{...standard.visual.background,base:p.backgroundColor}}/>
  <div style={{position:'absolute',left:portrait?54:78,top:portrait?178:96,width:portrait?972:1400,display:'flex',flexDirection:'column',gap:14,opacity:boardIntro*chrome}}>
   <div style={{color:p.accentColor,fontSize:portrait?29:24,fontWeight:600,letterSpacing:2}}>能力模型</div>
   <div style={{color:p.headingColor,fontSize:portrait?67:57,fontWeight:700,lineHeight:1.2}}>{p.title}</div>
  </div>
  <div style={{opacity:boardIntro,transformStyle:'preserve-3d',overflow:'visible'}}>
  <CameraWorld camera={camera}>
   <Sheet r={L.board} z={-12} material={{...paper,surface:'#F4ECF7',secondary:'#DFD1E7'}} elevation={4} opacity={nonfocus}>
    <div style={{display:'flex',alignItems:'baseline',gap:30,color:p.accentColor,fontSize:52,fontWeight:700}}><span>任务单</span><span style={{fontSize:34,fontWeight:500,opacity:.7}}>同一件事，两种能力</span></div>
    <div style={{height:3,background:p.accentColor,opacity:.17}}/>
   </Sheet>
   <Sheet r={L.self} z={12} material={paper} elevation={8} opacity={1-.94*(detailFocus-selfFocus)}>
    <div style={{fontSize:43,fontWeight:600,color:p.accentColor,lineHeight:1.2}}>个人能力</div>
    <div style={{display:'flex',flexDirection:portrait?'row':'column',alignItems:portrait?'center':'flex-start',gap:portrait?35:60,marginTop:portrait?12:60}}>
     <div style={{fontSize:portrait?108:97,fontWeight:700,lineHeight:1.12,color:p.inkColor,whiteSpace:'normal',maxWidth:portrait?700:400}}>{p.selfText}</div>
     <Tick size={portrait?107:140} color={p.accentColor} progress={done}/>
    </div>
    <div style={{...bodyStyle,color:p.inkColor,fontSize:portrait?45:43,marginTop:'auto'}}>任务由自己完成</div>
   </Sheet>
   <Sheet r={L.goal} z={12+16*lift.resource} material={paper} elevation={10} opacity={nonfocus}>
    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:25,color:p.accentColor,height:'100%'}}>
     <div style={{fontSize:portrait?65:64,fontWeight:700,lineHeight:1.15}}>{p.goalText}</div>
     <div style={{fontSize:portrait?45:43,fontWeight:500,color:p.inkColor}}>带队能力</div>
    </div>
   </Sheet>
   {/* The sheets are the same objects while lifted, visited and returned. */}
   <div style={{transformStyle:'preserve-3d',transform:`translateY(${-18*lift.resource}px)`}}>
    <Packet r={L.resource} z={12+170*lift.resource} shift={-46*lift.resource} caption={p.resourceText} detail={p.resourceDetail} p={p} active={resDone} opacity={1-.94*(detailFocus-resFocus)}/>
   </div>
   <div style={{transformStyle:'preserve-3d',transform:`translateY(${-22*lift.colleague}px)`}}>
    <Packet r={L.colleague} z={12+200*lift.colleague} shift={38*lift.colleague} caption={p.colleagueText} detail={p.colleagueDetail} p={p} active={colDone} opacity={1-.94*(detailFocus-colFocus)}/>
   </div>
   {/* Paths live in the document coordinate system and connect the named sheets. */}
   <svg width={L.board.w} height={L.board.h} viewBox={`0 0 ${L.board.w} ${L.board.h}`} style={{position:'absolute',left:0,top:0,transform:'translateZ(16px)',overflow:'visible',pointerEvents:'none',opacity:resultDone}}>
    {portrait?<path d="M295 1222 V1240 H550 V1255 M805 1222 V1240 H550" fill="none" stroke={p.accentColor} strokeWidth="6" strokeLinecap="round"/>:<path d="M893 727 V748 H1142 V770 M1393 727 V748 H1142" fill="none" stroke={p.accentColor} strokeWidth="6" strokeLinecap="round"/>}
   </svg>
   <Sheet r={L.result} z={12} material={{...paper,surface:'#FDF4FF',secondary:'#EDDAF4'}} elevation={9} opacity={nonfocus}>
    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:25,height:'100%'}}>
     <div style={{...bodyStyle,fontSize:portrait?70:62,fontWeight:700,color:p.accentColor}}>{p.resultText}</div>
     <Tick size={portrait?90:82} color={p.accentColor} progress={resultDone}/>
    </div>
   </Sheet>
  </CameraWorld>
  </div>
 </FullCanvas>;
}
