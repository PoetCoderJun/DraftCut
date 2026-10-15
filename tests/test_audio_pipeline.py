import copy, hashlib, json, math, subprocess, sys, tempfile, unittest, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_audio import prepare, propose_gaps, selected_deletions, validate_transcript
from validate_plan import validate

class AudioPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.audio=self.root/'input.wav'
        with wave.open(str(self.audio),'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100)
            w.writeframes(b''.join(int(3000*math.sin(i*2*math.pi*220/44100) if i<22050 or i>=66150 else 0).to_bytes(2,'little',signed=True) for i in range(88200)))
        self.transcript={'duration_seconds':2,'segments':[{'start':0,'end':.5,'text':'A','words':[{'start':0,'end':.5,'text':'A'}]},{'start':1.5,'end':2,'text':'B','words':[{'start':1.5,'end':2,'text':'B'}]}]}
        self.review={'audio_sha256':hashlib.sha256(self.audio.read_bytes()).hexdigest(),'gaps':[{'start':.5,'end':1.5,'kind':'breath','approved':True,'reason':'Synthetic gap selected for timing test, not an ASR breath detection.'}]}
    def tearDown(self):self.temp.cleanup()
    def test_no_trim_preserves_timeline_and_normalized_pcm(self):
        r=prepare(self.audio,self.transcript,self.root/'no',trim_breaths='no')
        self.assertEqual(r['duration_seconds'],2);self.assertEqual(r['selected_gaps'],0)
        self.assertEqual((self.root/'no/narration.wav').read_bytes(),(self.root/'no/normalized-source.wav').read_bytes())
        t=json.loads((self.root/'no/transcript.json').read_text());self.assertEqual(t['segments'][1]['start'],1.5)
    def test_selective_gap_to_quarter_second_and_srt_mapping(self):
        r=prepare(self.audio,self.transcript,self.root/'yes',trim_breaths='yes',review=self.review)
        self.assertEqual(json.loads((self.root/'yes/gap-review.json').read_text()),self.review)
        self.assertEqual(r['duration_seconds'],1.25);self.assertEqual(r['deletions_samples'],[(30000,66000)])
        t=json.loads((self.root/'yes/transcript.json').read_text());self.assertEqual(t['segments'][1]['start'],.75)
        self.assertEqual(t['segments'][1]['words'][0]['end'],1.25)
        self.assertIn('00:00:00,750 --> 00:00:01,250',(self.root/'yes/final.srt').read_text())
    def test_candidates_never_auto_approve(self):
        p=propose_gaps(self.transcript);self.assertEqual(p['gaps'][0]['kind'],'unclassified');self.assertFalse(p['gaps'][0]['approved'])
    def test_unapproved_pause_preserved(self):
        self.review['gaps'][0]['approved']=False
        r=prepare(self.audio,self.transcript,self.root/'pause',trim_breaths='yes',review=self.review);self.assertEqual(r['duration_seconds'],2)
    def test_speech_overlap_and_wrong_source_rejected(self):
        self.review['gaps'][0]['start']=.4
        with self.assertRaisesRegex(ValueError,'overlaps speech'):selected_deletions(self.transcript,self.review,2,.25)
        self.review['audio_sha256']='wrong'
        with self.assertRaisesRegex(ValueError,'SHA-256'):prepare(self.audio,self.transcript,self.root/'wrong',trim_breaths='yes',review=self.review)
    def test_explicit_decision_and_listening_review_required(self):
        for choice,review in [('maybe',None),('yes',None),('no',self.review)]:
            with self.assertRaises(ValueError):prepare(self.audio,self.transcript,self.root/'invalid',trim_breaths=choice,review=review)
    def test_nan_and_source_mismatch_rejected(self):
        for duration in [float('nan'),3]:
            t=copy.deepcopy(self.transcript);t['duration_seconds']=duration
            with self.assertRaises(ValueError):validate_transcript(t,2)
    def test_cloud_asr_without_consent_cannot_start(self):
        p=subprocess.run([sys.executable,str(ROOT/'scripts/transcribe_audio.py'),'--audio',str(self.audio),'--output-dir',str(self.root/'asr'),'--trim-breaths','no'],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('Obtain authorization',p.stderr);self.assertFalse((self.root/'asr').exists())
    def test_approved_audio_plan_without_optional_assets(self):
        p=json.loads((ROOT/'examples/plan-validation/plan.json').read_text());self.assertEqual(validate(p),[])
        del p['workflow'];self.assertTrue(any('migration' in e for e in validate(p)))
    def test_production_export_blocks_unfinished_scaffold(self):
        project=self.root/'unfinished';project.mkdir();(project/'project-state.json').write_text(json.dumps({'status':'scaffold','needs_visual_production':True}))
        p=subprocess.run(['node',str(ROOT/'scripts/render_master.mjs'),'--project-dir',str(project),'--plan',str(ROOT/'examples/plan-validation/plan.json'),'--output',str(self.root/'output.mp4')],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('Complete the approved visual production',p.stderr);self.assertFalse((self.root/'output.mp4').exists())
    def test_nonexistent_review_evidence_blocks_export(self):
        project=self.root/'review';project.mkdir();(project/'project-state.json').write_text(json.dumps({'status':'ready','needs_visual_production':False,'visual_review':{'scope':'continuous','evidence':['missing.md']}}))
        p=subprocess.run(['node',str(ROOT/'scripts/render_master.mjs'),'--project-dir',str(project),'--plan',str(ROOT/'examples/plan-validation/plan.json'),'--output',str(self.root/'output.mp4')],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('evidence does not exist',p.stderr)
    def test_legacy_prepared_audio_requires_explicit_migration(self):
        r=prepare(self.audio,self.transcript,self.root/'prepared',trim_breaths='no')
        plan={'approved':True,'status':'approved','source':{'audio':r['audio'],'subtitles':r['subtitles']}}
        path=self.root/'legacy.json';path.write_text(json.dumps(plan))
        project=self.root/'project'
        cmd=['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(path),'--project-dir',str(project)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('migration',p.stderr);self.assertFalse(project.exists())
        self.assertTrue(Path(r['audio']).exists())

if __name__=='__main__':unittest.main()
