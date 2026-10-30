# -*- coding: utf-8 -*-
"""Synthetic regressions. No external research, generation, native render or taste claim."""
import copy,io,json,struct,subprocess,sys,tempfile,unittest,zlib
from pathlib import Path
import material_gate as g

def png(path,alphas):
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 pixels=b''.join(bytes([60,80,120,a]) for a in alphas)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',len(alphas),1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+pixels))+chunk(b'IEND',b''))

class Materials(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for name in ['source.bin','receipt.json','logic.tsx','generation.json','native.json','preview.bin','final.mp4']:(self.root/name).write_text('Synthetic fixture only: '+name)
  for name,alpha in [('cutout.png',[0,255,255,0]),('opaque.png',[255]*4),('empty.png',[0]*4)]:png(self.root/name,alpha)
  self.p=g.template();self.p.update(template_only=False,input_mode='screen_explainer',canvas={'width':1080,'height':1920,'fps':30})
  self.p['research_receipts']=[{'id':'r','kind':'provided','query_or_inspection':'Inspect actual screen action fixture','source':'User-supplied recording fixture','date':'2026-10-30','result':'provided-sufficient','evidence':self.file('receipt.json')}]
  self.p['materials']=[{'id':'real','tier':'real','role':'evidence',**self.file('source.bin'),'source':'Provided screen fixture','rights_boundary':'Synthetic task-only fixture','availability':'collected'},{'id':'code','tier':'code','role':'label',**self.file('logic.tsx'),'rights_boundary':'Synthetic exact label fixture','availability':'collected'}]
  self.p['scenes']=[{'id':'S01','source_mode':'screen_explainer','master_range_frames':[0,90],'goal':'Locate one real screen control','presentation':'transparent_overlay','research_ids':['r'],'material_ids':['real','code'],'tier1_assessment':'Provided screen is sufficient for the visible action','tier2_assessment':'Existing real screen fully covers target; no generation needed','code_reason':'Only a number/arrow on the actual control','composition_plan':{'opening':'Actual recording','focus':'Actual source ROI for the button','reading':'Hold true feedback until visible','handoff':'Remove arrow before the next action','spatial_treatment':'Keep original camera for this small overlay; no separate 3D scene','motion_purpose':'Guide the action without covering feedback'},'mobile_readability_plan':'Inspect target and native captions at 360-390px width','protected_regions_reference':'Current screen control, feedback and caption areas','source_clock_reference':'Original recording mapping, same master source clock'}]
 def tearDown(self):self.temp.cleanup()
 def file(self,name):return {'file':str(self.root/name),'sha256':g.digest(self.root/name)}
 def save(self,p=None):
  path=self.root/'plan.json';path.write_text(json.dumps(p or self.p));return path
 def check(self,ok,p=None,phase='before-mg'):
  result=g.check_plan(self.save(p),phase);self.assertEqual(result['ok'],ok,result);return result
 def generated(self,p=None):
  p=p or self.p;p.update(input_mode='face_talking_head');p['research_receipts'][0].update(kind='online',query_or_inspection='Actual conceptual-object search fixture',source='https://example.test/original',result='unsuitable')
  p['materials']=[{'id':'image','tier':'generated','role':'illustration',**self.file('cutout.png'),'rights_boundary':'Conceptual fixture only','availability':'collected','generation_record':self.file('generation.json'),'visual_review':'Fixture declaration; no beauty claim'},p['materials'][1]]
  p['scenes'][0].update(source_mode='face_talking_head',presentation='professional_mg',material_ids=['image','code'],tier1_assessment='Actual-search fixture did not give a suitable object',tier2_assessment='Concept cutout adds explanatory value',code_reason='Only exact relations')
  return p
 def delivered(self):
  for a in self.p['materials']:a['availability']='used'
  s=self.p['scenes'][0];s.update(native_binding_evidence=self.file('native.json'),native_preview_evidence=self.file('preview.bin'),mobile_review={'status':'pass','finding':'Synthetic evidence identity only','evidence':self.file('preview.bin')});self.p['final_output']=self.file('final.mp4')
 def handoff(self):
  plan=self.save();s=self.p['scenes'][0];d={'template_only':False,'master':{'input_mode':self.p['input_mode'],'canvas_size':[1080,1920],'fps':30},'material_preparation':{'policy_id':g.POLICY,'plan':self.file(plan.name)},'scenes':[{'scene_id':'S01','master_range_frames':s['master_range_frames'],'material_preparation':{'applicable':True,'plan_scene_id':'S01','current_material_ids':s['material_ids']}}]}
  p=self.root/'handoff.json';p.write_text(json.dumps(d));return p,d
 def test_existing_screen_needs_no_online_or_generation(self):self.check(True)
 def test_concept_real_search_then_actual_alpha(self):self.generated();r=self.check(True);self.assertEqual(r['png_alpha_audits'][0]['transparentFraction'],.5)
 def test_no_research_or_inspection(self):self.p['research_receipts']=[];self.check(False)
 def test_only_presenter_cannot_bypass_online_search(self):self.p['materials'][0]['role']='presenter';self.check(False)
 def test_code_only_without_real_search(self):self.p['scenes'][0]['material_ids']=['code'];self.check(False)
 def test_opaque_png_rejected(self):self.generated();self.p['materials'][0].update(self.file('opaque.png'));self.check(False)
 def test_empty_png_rejected(self):self.generated();self.p['materials'][0].update(self.file('empty.png'));self.check(False)
 def test_generated_evidence_rejected(self):self.generated();self.p['materials'][0]['role']='evidence';self.check(False)
 def test_missing_generation_record_rejected(self):self.generated();self.p['materials'][0]['generation_record']=None;self.check(False)
 def test_changed_material_rejected(self):self.p['materials'][0]['sha256']='0'*64;self.check(False)
 def test_tier_two_assessment_required(self):self.p['scenes'][0]['tier2_assessment']='';self.check(False)
 def test_camera_checkbox_is_not_a_plan(self):self.p['scenes'][0]['composition_plan']={k:True for k in self.p['scenes'][0]['composition_plan']};self.check(False)
 def test_phone_reading_plan_required(self):self.p['scenes'][0]['mobile_readability_plan']='';self.check(False)
 def test_mode_mismatch_rejected(self):self.p['scenes'][0]['source_mode']='face_talking_head';self.check(False)
 def test_mixed_can_use_per_scene_source_mode(self):self.p['input_mode']='mixed';self.check(True)
 def test_frame_range_required(self):self.p['scenes'][0]['master_range_frames']=[90,0];self.check(False)
 def test_delivery_needs_actual_native_and_mobile_evidence(self):self.check(False,phase='delivery')
 def test_complete_delivery_identity_fixture(self):self.delivered();self.check(True,phase='delivery')
 def test_collected_is_not_used(self):self.delivered();self.p['materials'][0]['availability']='collected';self.check(False,phase='delivery')
 def test_current_handoff_binding_passes(self):p,_=self.handoff();self.assertTrue(g.check_handoff(p)['ok'])
 def test_delivery_handoff_binding_passes(self):self.delivered();p,_=self.handoff();self.assertTrue(g.check_handoff(p,'delivery')['ok'])
 def test_stale_plan_hash_rejected(self):p,_=self.handoff();self.save().write_text('{}');self.assertFalse(g.check_handoff(p)['ok'])
 def test_stale_handoff_material_ids_rejected(self):p,d=self.handoff();d['scenes'][0]['material_preparation']['current_material_ids']=[];p.write_text(json.dumps(d));self.assertFalse(g.check_handoff(p)['ok'])
 def test_missing_current_scene_rejected(self):self.assertFalse(g.check_plan(self.save(),required_scenes=['new-scene'])['ok'])
 def test_wrong_canvas_rejected(self):p,d=self.handoff();d['master']['canvas_size']=[1920,1080];p.write_text(json.dumps(d));self.assertFalse(g.check_handoff(p)['ok'])
 def test_existing_handoff_object_frame_range_is_compatible(self):p,d=self.handoff();d['scenes'][0]['master_range_frames']={'start_inclusive':0,'end_exclusive':90};p.write_text(json.dumps(d));self.assertTrue(g.check_handoff(p)['ok'])
 def test_plan_object_frame_range_matches_existing_template(self):self.p['scenes'][0]['master_range_frames']={'start_inclusive':0,'end_exclusive':90};self.check(True);p,_=self.handoff();self.assertTrue(g.check_handoff(p)['ok'])
 def test_different_object_frame_range_rejected(self):p,d=self.handoff();d['scenes'][0]['master_range_frames']={'start_inclusive':1,'end_exclusive':90};p.write_text(json.dumps(d));self.assertFalse(g.check_handoff(p)['ok'])
 def test_wrong_object_range_keys_rejected(self):self.p['scenes'][0]['master_range_frames']={'from':0,'to':90};self.check(False)
 def test_wrong_current_frame_range_rejected(self):p,d=self.handoff();d['scenes'][0]['master_range_frames']=[90,180];p.write_text(json.dumps(d));self.assertFalse(g.check_handoff(p)['ok'])
 def test_not_applicable_needs_reason(self):p,d=self.handoff();d['scenes'].append({'scene_id':'plain','material_preparation':{'applicable':False}});p.write_text(json.dumps(d));self.assertFalse(g.check_handoff(p)['ok'])
 def test_plain_unchanged_scene_can_be_excluded(self):p,d=self.handoff();d['scenes'].append({'scene_id':'plain','material_preparation':{'applicable':False,'reason_if_not_applicable':'Unchanged real screen, no new explanation animation'}});p.write_text(json.dumps(d));self.assertTrue(g.check_handoff(p)['ok'])
 def test_actual_provenance_required(self):self.p['materials'][0]['source']=None;self.check(False)
 def test_explicit_full_background_exception(self):self.generated();self.p['materials'][0].update(**self.file('opaque.png'),full_background_exception={'reason':'Synthetic explicit full scene request','request_evidence':self.file('receipt.json')});self.check(True)
 def test_background_exception_needs_request(self):self.generated();self.p['materials'][0].update(**self.file('opaque.png'),full_background_exception={'reason':'Assumed full scene'});self.check(False)
 def test_old_policy_hash_rejected(self):self.p['policy_hash']='old';self.check(False)
 def test_cli_prepare_is_not_completion(self):
  target=self.root/'new-plan.json';cmd=[sys.executable,str(g.ROOT/'scripts/material_gate.py'),'prepare','--output',str(target)];r=subprocess.run(cmd,cwd=self.root,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(g.check_plan(target)['ok']);self.assertTrue(json.loads(r.stdout)['required_reading'].endswith('material-preparation.md'))
 def test_cli_never_overwrites_plan(self):
  target=self.save();before=target.read_bytes();r=subprocess.run([sys.executable,str(g.ROOT/'scripts/material_gate.py'),'prepare','--output',str(target)],capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(before,target.read_bytes())

def main():
 stream=io.StringIO();r=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromTestCase(Materials));out={'ok':r.wasSuccessful(),'tests_run':r.testsRun,'failures':[str(t)+': '+s for t,s in r.failures+r.errors],'scope':'Synthetic receipts, files, alpha, source modes and current handoff checks only. No real search, generation, video playback, listening or user aesthetic approval.'};print(json.dumps(out,ensure_ascii=False,indent=2));return 0 if out['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
