# -*- coding: utf-8 -*-
"""Short-video material readiness and current-handoff checks; not taste tests.

The packaged PNG alpha decoder is adapted from course-long-video-editing 1.8.0.
No runtime dependency on that Skill, networking, generation or native mutation.
"""
import argparse,hashlib,json,math,struct,zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY='real-first-png-logic-2026-10-30'
MODES={'face_talking_head','screen_explainer','mixed'}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def policy_hash():
 files=['references/material-preparation.md','scripts/material_gate.py']
 return hashlib.sha256(json.dumps({n:digest(ROOT/n) for n in files},sort_keys=True).encode()).hexdigest()
def text_value(v):return isinstance(v,str) and bool(v.strip())
def checked(row,base,errors,label):
 if not isinstance(row,dict) or not text_value(row.get('file')) or not text_value(row.get('sha256')):
  errors.append(label+': file/sha256 required');return None
 p=(base/row['file']).resolve()
 if not p.is_file():errors.append(label+': file missing');return None
 if digest(p)!=row['sha256']:errors.append(label+': file changed');return None
 return p
def frame_range(value):
 if isinstance(value,dict):value=[value.get('start_inclusive'),value.get('end_exclusive')]
 if not isinstance(value,list) or len(value)!=2 or any(isinstance(x,bool) or not isinstance(x,int) for x in value) or value[0]<0 or value[1]<=value[0]:return None
 return value
def indexed(rows,errors,label):
 if not isinstance(rows,list) or any(not isinstance(x,dict) for x in rows):
  errors.append(label+': object array required');return {}
 if any(not text_value(x.get('id')) for x in rows):errors.append(label+': nonempty IDs required');return {}
 by={x['id']:x for x in rows}
 if len(by)!=len(rows):errors.append(label+': duplicate IDs')
 return by
def id_list(value,known,errors,label):
 if not isinstance(value,list) or not value or any(not text_value(x) for x in value):
  errors.append(label+': nonempty ID list required');return []
 if len(value)!=len(set(value)) or not set(value)<=set(known):errors.append(label+': duplicate or unknown IDs')
 return value

def png_alpha(p):
 """Decode 8-bit noninterlaced RGBA/GA PNG filters, without optional packages."""
 b=Path(p).read_bytes()
 if not b.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Expected PNG bytes')
 pos=8;chunks=[];info=None
 while pos+12<=len(b):
  n=struct.unpack('>I',b[pos:pos+4])[0];typ=b[pos+4:pos+8];data=b[pos+8:pos+8+n]
  if len(data)!=n:raise ValueError('Truncated PNG')
  if zlib.crc32(typ+data)&0xffffffff!=struct.unpack('>I',b[pos+8+n:pos+12+n])[0]:raise ValueError('PNG checksum mismatch')
  if typ==b'IHDR':info=struct.unpack('>IIBBBBB',data)
  elif typ==b'IDAT':chunks.append(data)
  pos+=12+n
  if typ==b'IEND':break
 if not info:raise ValueError('Missing PNG IHDR')
 w,h,depth,color,compression,filter_method,interlace=info
 if not w or not h or w*h>25000000:raise ValueError('PNG size outside audit bounds')
 if depth!=8 or color not in (4,6) or interlace or compression or filter_method:
  raise ValueError('Use a verified 8-bit noninterlaced RGBA/GA cutout PNG for alpha audit')
 step=4 if color==6 else 2;stride=w*step
 raw=zlib.decompress(b''.join(chunks))
 if len(raw)!=(stride+1)*h:raise ValueError('PNG decoded size mismatch')
 prev=bytearray(stride);hist=[0]*256
 def paeth(a,b,c):
  v=a+b-c;aa=abs(v-a);bb=abs(v-b);cc=abs(v-c)
  return a if aa<=bb and aa<=cc else b if bb<=cc else c
 for y in range(h):
  off=y*(stride+1);mode=raw[off];row=bytearray(raw[off+1:off+1+stride])
  if mode>4:raise ValueError('Invalid PNG filter')
  for x in range(stride):
   a=row[x-step] if x>=step else 0;up=prev[x];ul=prev[x-step] if x>=step else 0
   add=0 if mode==0 else a if mode==1 else up if mode==2 else (a+up)//2 if mode==3 else paeth(a,up,ul)
   row[x]=(row[x]+add)&255
  for a in row[step-1::step]:hist[a]+=1
  prev=row
 lo=next(i for i,n in enumerate(hist) if n);hi=next(i for i in range(255,-1,-1) if hist[i])
 return {'width':w,'height':h,'alphaMin':lo,'alphaMax':hi,'transparentFraction':hist[0]/(w*h)}

def template():
 return {'schema_version':1,'template_only':True,'policy_id':POLICY,'policy_hash':policy_hash(),'input_mode':None,
 'canvas':{'width':None,'height':None,'fps':None},'research_receipts':[],'materials':[],'scenes':[],
 'receipt_template':{'id':None,'kind':'online|provided','query_or_inspection':None,'source':None,'date':None,'result':'collected|unavailable|unsuitable|provided-sufficient|provided-insufficient','evidence':{'file':None,'sha256':None}},
 'material_template':{'id':None,'tier':'real|generated|code','role':'evidence|illustration|identity|context|presenter|logic|label|relation','file':None,'sha256':None,'source':None,'rights_boundary':None,'availability':'collected|imported-reference|used','generation_record':None,'visual_review':None,'full_background_exception':None},
 'scene_template':{'id':None,'source_mode':None,'master_range_frames':{'start_inclusive':None,'end_exclusive':None},'goal':None,'presentation':'professional_mg|transparent_overlay','research_ids':[],'material_ids':[],'tier1_assessment':None,'tier2_assessment':None,'code_reason':None,'composition_plan':{'opening':None,'focus':None,'reading':None,'handoff':None,'spatial_treatment':None,'motion_purpose':None},'mobile_readability_plan':None,'protected_regions_reference':None,'source_clock_reference':None,'native_binding_evidence':None,'native_preview_evidence':None,'mobile_review':None},
 'final_output':None,'scope':'Assistant fills actual records and sets template_only=false. Planning/file checks cannot certify actual source truth, permissions, beauty, listening or user approval.'}

def check_plan(path,phase='before-mg',required_scenes=None):
 path=Path(path).resolve();base=path.parent;d=json.loads(path.read_text());errors=[];alpha_audits=[]
 if d.get('schema_version')!=1 or d.get('template_only') is not False:errors.append('Fill actual plan; template is not readiness evidence')
 if d.get('policy_id')!=POLICY or d.get('policy_hash')!=policy_hash():errors.append('Material rules/checker changed; review the current policy and prepare an updated version')
 mode=d.get('input_mode')
 if mode not in MODES:errors.append('Actual input_mode required')
 canvas=d.get('canvas') or {}
 for key in ['width','height','fps']:
  value=canvas.get(key)
  if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:errors.append('Actual positive canvas/'+key+' required')
 receipts=indexed(d.get('research_receipts'),errors,'research_receipts')
 if not receipts:errors.append('Actual online research or sufficient-source inspection receipts required')
 for rid,r in receipts.items():
  if not all(text_value(r.get(k)) for k in ['query_or_inspection','source','date']):errors.append(rid+': actual query/inspection, source and date required')
  allowed={'online':{'collected','unavailable','unsuitable'},'provided':{'provided-sufficient','provided-insufficient'}}
  if r.get('kind') not in allowed or r.get('result') not in allowed.get(r.get('kind'),set()):errors.append(rid+': explicit research kind and actual result required')
  checked(r.get('evidence'),base,errors,rid+'/receipt')
 materials=indexed(d.get('materials'),errors,'materials')
 for aid,a in materials.items():
  tier=a.get('tier');role=a.get('role');p=checked(a,base,errors,aid)
  if tier not in {'real','generated','code'}:errors.append(aid+': unknown tier')
  if not text_value(a.get('rights_boundary')):errors.append(aid+': usage/rights boundary missing')
  if a.get('availability') not in {'collected','imported-reference','used'}:errors.append(aid+': only actually received material belongs in active plan; failed searches stay in receipts')
  if tier=='real' and not text_value(a.get('source')):errors.append(aid+': actual source/provenance missing')
  if tier=='real' and role not in {'evidence','illustration','identity','screen','context','presenter'}:errors.append(aid+': explicit actual real-material role required')
  if tier=='generated':
   if role!='illustration':errors.append(aid+': generated content cannot be factual evidence')
   checked(a.get('generation_record'),base,errors,aid+'/generation')
   if not text_value(a.get('visual_review')):errors.append(aid+': actual subject/edge/light visual review required')
   exception=a.get('full_background_exception')
   if exception:
    if not isinstance(exception,dict) or not text_value(exception.get('reason')):errors.append(aid+': explicit full-background request reason required')
    else:checked(exception.get('request_evidence'),base,errors,aid+'/full-background-request')
   elif p:
    try:
     q=png_alpha(p);alpha_audits.append({'id':aid,**q})
     if q['alphaMin']>=255 or q['alphaMax']<=0 or not .001<q['transparentFraction']<.995:errors.append(aid+': visible subject and actual transparent background required')
    except (ValueError,struct.error,zlib.error) as e:errors.append(aid+': '+str(e))
  if tier=='code' and role not in {'logic','label','relation'}:errors.append(aid+': code content must serve logic, relation or exact labels')
 scenes=indexed(d.get('scenes'),errors,'scenes')
 if not scenes:errors.append('Current explanation-scene inventory required')
 if required_scenes is not None and set(scenes)!=set(required_scenes):errors.append('Material plan and applicable current handoff scenes differ')
 for sid,s in scenes.items():
  sm=s.get('source_mode')
  if sm not in MODES or (mode in MODES-{'mixed'} and sm!=mode):errors.append(sid+': source mode differs from current input')
  span=frame_range(s.get('master_range_frames'))
  if span is None:errors.append(sid+': actual ordered master frame range required')
  if s.get('presentation') not in {'professional_mg','transparent_overlay'}:errors.append(sid+': actual presentation type required')
  if not all(text_value(s.get(k)) for k in ['goal','tier1_assessment','tier2_assessment','mobile_readability_plan','protected_regions_reference','source_clock_reference']):errors.append(sid+': goal, tier assessments, phone readability, protection and source-clock plan required')
  ids=id_list(s.get('material_ids'),materials,errors,sid+'/materials');rids=id_list(s.get('research_ids'),receipts,errors,sid+'/research')
  real=[materials[x] for x in ids if x in materials and materials[x].get('tier')=='real' and materials[x].get('role') not in {'context','presenter'}]
  online=any(receipts.get(x,{}).get('kind')=='online' for x in rids)
  sufficient=any(receipts.get(x,{}).get('kind')=='provided' and receipts.get(x,{}).get('result')=='provided-sufficient' for x in rids)
  if not online and not (real and sufficient):errors.append(sid+': lower-tier-only scene needs real online research; a presenter/background alone does not replace explanatory material')
  if any(materials.get(x,{}).get('tier')=='code' for x in ids) and not text_value(s.get('code_reason')):errors.append(sid+': explain code logic role after evaluating real material and PNG')
  camera=s.get('composition_plan') or {}
  if not all(text_value(camera.get(k)) for k in ['opening','focus','reading','handoff','spatial_treatment','motion_purpose']):errors.append(sid+': specific framing/focus/reading/depth/motion plan required; short overlays may state why camera stays on real screen')
  if phase=='delivery':
   for aid in ids:
    if materials.get(aid,{}).get('availability')!='used':errors.append(sid+': selected material not recorded actually used: '+aid)
   checked(s.get('native_binding_evidence'),base,errors,sid+'/native-binding')
   checked(s.get('native_preview_evidence'),base,errors,sid+'/actual-composition')
   m=s.get('mobile_review') or {}
   if m.get('status')!='pass' or not text_value(m.get('finding')):errors.append(sid+': actual phone-width reading review required')
   checked(m.get('evidence'),base,errors,sid+'/phone-reading')
 if phase=='delivery':checked(d.get('final_output'),base,errors,'current-final-output')
 return {'ok':not errors,'errors':errors,'phase':phase,'scenes':len(scenes),'materials':len(materials),'png_alpha_audits':alpha_audits,'scope':'File/alpha/provenance declarations and coverage only; inspect source truth, licenses, native camera/video motion, mobile pixels, listening and current user acceptance separately.'}

def check_handoff(path,phase='before-mg'):
 path=Path(path).resolve();base=path.parent;d=json.loads(path.read_text());errors=[]
 if d.get('template_only') is not False:errors.append('Actual handoff required; template is not a project')
 scope=d.get('material_preparation') or {}
 if scope.get('policy_id')!=POLICY:errors.append('Current handoff material policy missing')
 p=checked(scope.get('plan'),base,errors,'handoff/material-plan')
 rows=d.get('scenes');ids=[];by={}
 if not isinstance(rows,list) or not rows:errors.append('Current handoff scenes required');rows=[]
 for s in rows:
  sid=s.get('scene_id') if isinstance(s,dict) else None
  if not text_value(sid) or sid in by:errors.append('Unique current handoff scene IDs required');continue
  by[sid]=s;applies=s.get('material_preparation') or {}
  if applies.get('applicable') is False:
   if not text_value(applies.get('reason_if_not_applicable')):errors.append(sid+': explicit non-applicable scope reason required')
  elif applies.get('applicable') is True:
   ids.append(sid)
   if applies.get('plan_scene_id')!=sid:errors.append(sid+': map the same plan scene ID')
  else:errors.append(sid+': actual material applicability must be explicit')
 if not ids:errors.append('No applicable new explanation scenes; do not run material gate for an unrelated/local-only task')
 result=None
 if p:
  result=check_plan(p,phase,ids);errors+=result['errors'];plan=json.loads(p.read_text());master=d.get('master') or {}
  if master.get('input_mode')!=plan.get('input_mode'):errors.append('Handoff/plan input mode mismatch')
  if master.get('canvas_size')!=[plan.get('canvas',{}).get('width'),plan.get('canvas',{}).get('height')] or master.get('fps')!=plan.get('canvas',{}).get('fps'):errors.append('Handoff/plan actual canvas or fps mismatch')
  for s in plan.get('scenes',[]):
   h=by.get(s['id'],{});a=h.get('material_preparation') or {}
   if frame_range(h.get('master_range_frames'))!=frame_range(s.get('master_range_frames')):errors.append(s['id']+': handoff/plan frame range mismatch')
   if a.get('current_material_ids')!=s.get('material_ids'):errors.append(s['id']+': handoff material IDs are stale')
 return {'ok':not errors,'errors':errors,'phase':phase,'applicable_scene_count':len(ids),'plan_check':result,'scope':'Current plan binding and preparation/delivery evidence; cannot authorize external actions or certify aesthetics.'}

def main():
 parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='command',required=True)
 p=subs.add_parser('prepare');p.add_argument('--output',required=True)
 p=subs.add_parser('check');g=p.add_mutually_exclusive_group(required=True);g.add_argument('--plan');g.add_argument('--handoff');p.add_argument('--phase',choices=['before-mg','delivery'],default='before-mg')
 args=parser.parse_args()
 try:
  if args.command=='prepare':
   out=Path(args.output).expanduser().resolve()
   if out==ROOT or ROOT in out.parents:raise ValueError('Write the task plan outside the installed Skill')
   if out.exists():raise ValueError('Output exists; preserve it and choose a new version')
   out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(template(),ensure_ascii=False,indent=2)+'\n')
   result={'ok':True,'file':str(out),'required_reading':str(ROOT/'references/material-preparation.md'),'state':'template-not-prepared-materials'}
  elif args.handoff:result=check_handoff(args.handoff,args.phase)
  else:result=check_plan(args.plan,args.phase)
 except (OSError,ValueError,KeyError,TypeError,AttributeError) as e:result={'ok':False,'errors':[str(e)]}
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
