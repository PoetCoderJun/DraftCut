"""Simulation receipts exercise the workflow without ever authorizing production."""
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from example_fixture import fixture
from spoken_edit import initialize,read,write,sha
from spoken_workflow import preview,record_capabilities,manuscript_request,render_audio,director_request,assert_director,ApprovalRequired
from simulation import create,attach,approve,context
from review_approval import verify_receipt,issue

class SimulationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);audio,t,_=fixture();self.source=self.root/'source.wav';self.source.write_bytes(audio);self.transcript=self.root/'transcript.json';write(self.transcript,t)
  self.run_file=create(self.source,self.root/'run');self.p=self.root/'run/projects/project';m=initialize(self.source,self.transcript,self.p);write(self.p/'source.json',attach(self.p,m,self.run_file))
  d=read(self.p/'manuscript.json');d['reviewed_word_ids']=d['order'];d['caption_groups']=[d['order'][i:i+3] for i in range(0,len(d['order']),3)];write(self.p/'manuscript.json',d);preview(self.p);record_capabilities(self.p,'unavailable','Audio input unavailable in this simulation')
 def tearDown(self):self.tmp.cleanup()
 def first(self):
  q,f,t=manuscript_request(self.p);approve(f/'request.json','这版口播可以，继续吧。');return q,f,t,render_audio(self.p)
 def second(self):
  q,f,t,loc=self.first();duration=t['duration_seconds'];plan=read(ROOT/'examples/plan-validation/plan.json');plan['example_only']=False
  script=self.p/'MG导演脚本.md';script.write_text('用数量图解释口播，保留否定和有意重复。')
  plan.update(source={'audio':str(loc/'narration.wav'),'subtitles':str(loc/'final.srt'),'duration_seconds':duration},workflow={'schema':'draftcut.workflow.v2','project_dir':str(self.p),'director_script':str(script)},cues=[{'id':'all','start_seconds':0,'end_seconds':round(duration*30)/30,'visual_prompt':'用图形解释原话。'}])
  path=self.p/'director-plan.json';write(path,plan);q,f,_,_=director_request(path);approve(f/'request.json','这个视频脚本没问题，做吧。');return path
 def test_01_no_confirmation_still_blocks_test_audio(self):
  with self.assertRaises(ApprovalRequired):render_audio(self.p)
  self.assertFalse((self.p/'prepared').exists())
 def test_02_simulation_is_honest_and_not_a_production_receipt(self):
  q,f,t,loc=self.first();a=read(f/'approval.json');self.assertEqual(a['payload']['actor'],'simulated-user');self.assertFalse(a['payload']['owner_approval']);self.assertEqual(read(self.p/'semantic-review.json')['source_listened_seconds'],0)
  run,public=context(self.p,read(self.p/'source.json'))
  with self.assertRaisesRegex(ValueError,'forged|stale'):verify_receipt(q,a,public)
  with self.assertRaisesRegex(ValueError,'Production owner'):issue(q,'unused','unused')
  self.assertFalse(read(loc/'audio-preparation-report.json')['owner_approval'])
 def test_03_source_and_run_boundary_are_checked(self):
  m=read(self.p/'source.json')
  with self.assertRaisesRegex(ValueError,'boundary'):context(self.root/'elsewhere',m)
  m['source_sha256']='wrong'
  with self.assertRaisesRegex(ValueError,'different source'):context(self.p,m)
 def test_04_simulation_evidence_cannot_enter_a_production_project(self):
  m=read(self.p/'source.json');m.pop('simulation_run');write(self.p/'source.json',m);preview(self.p)
  e=read(self.p/'semantic-review.json');from spoken_workflow import manuscript_base
  e.update(manuscript_digest=manuscript_base(self.p),preview_sha256=read(self.p/'preview.json')['audio_sha256']);write(self.p/'semantic-review.json',e)
  with self.assertRaisesRegex(ValueError,'production review'):manuscript_request(self.p)
 def test_05_both_stages_and_edit_invalidation_are_real(self):
  plan=self.second();self.assertFalse(assert_director(plan)['owner_approval']);q,f,_,_=director_request(plan);old=read(f/'approval.json')
  script=self.p/'MG导演脚本.md';script.write_text(script.read_text()+' 增加一个图解。')
  with self.assertRaises(ApprovalRequired):assert_director(plan)
  q,new,_,_=director_request(plan);write(new/'approval.json',old)
  with self.assertRaisesRegex(ValueError,'stale'):assert_director(plan)
 def test_06_real_manuscript_change_cannot_reuse_test_confirmation(self):
  self.first();d=read(self.p/'manuscript.json');d['revision']+=1;d['decisions'][0]['reason']='Revised';write(self.p/'manuscript.json',d)
  with self.assertRaisesRegex(ValueError,'stale'):render_audio(self.p)
  preview(self.p);record_capabilities(self.p,'unavailable','still unavailable')
  with self.assertRaises(ApprovalRequired):render_audio(self.p)
 def test_07_scaffold_and_renderer_preserve_test_scope(self):
  plan=self.second();comp=self.p/'hyperframes';r=subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(plan),'--project-dir',str(comp)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn('SIMULATED USER TEST',(comp/'index.html').read_text())
  (comp/'test-evidence.md').write_text('Synthetic boundary test: production export must reject the simulation identity.')
  write(comp/'project-state.json',{'status':'ready','needs_visual_production':False,'visual_review':{'scope':'continuous','evidence':['test-evidence.md']}})
  r=subprocess.run(['node',str(ROOT/'scripts/render_master.mjs'),'--plan',str(plan),'--project-dir',str(comp),'--output',str(self.p/'final/video.mp4')],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('cannot authorize production',r.stderr)
  r=subprocess.run(['node',str(ROOT/'scripts/render_master.mjs'),'--purpose','simulation','--plan',str(plan),'--project-dir',str(comp),'--output',str(self.p/'final/video.mp4')],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('TEST-',r.stderr)
  html=comp/'index.html';html.write_text(html.read_text().replace('id="draftcut-test-watermark"','id="removed"'))
  with self.assertRaisesRegex(ValueError,'watermark'):assert_director(plan,comp)
 def test_08_capability_check_does_not_create_production_listening(self):
  (self.p/'semantic-review.json').unlink();m=read(self.p/'source.json');m.pop('simulation_run');write(self.p/'source.json',m);preview(self.p);record_capabilities(self.p,'unavailable','No audio input')
  self.assertFalse((self.p/'semantic-review.json').exists());self.assertEqual(read(self.p/'capabilities.json')['hearing'],'not-tested')

if __name__=='__main__':unittest.main()
