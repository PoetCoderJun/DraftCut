import copy,importlib.util,json,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('full_workflow_example',ROOT/'examples/full-workflow/run.py');example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
from spoken_edit import compile_edit,read,write,sha,verify_splice,render_presenter,source_state
from spoken_workflow import manuscript_request,render_audio,director_request,assert_director,preview,manuscript_base,ApprovalRequired
from review_approval import issue

class SpokenWorkflowTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.out=Path(self.temp.name)/'case'
    def tearDown(self):self.temp.cleanup()
    def draft(self):return example.draft_example(self.out)
    def complete(self):return example.complete_example(self.out)
    def test_01_manuscript_blocks_before_any_approved_audio(self):
        p,k=self.draft()
        with self.assertRaisesRegex(ApprovalRequired,'spoken manuscript'):render_audio(p)
        self.assertFalse((p/'prepared').exists())
        q,f,t=manuscript_request(p);self.assertIn('三十',(f/'review.md').read_text());self.assertIn('SENSITIVE',(f/'review.md').read_text())
    def test_02_signed_manuscript_actual_pcm_deletes_retakes_keeps_meaning(self):
        p,k=self.draft();q,f,t=manuscript_request(p);example.approve_fixture(q,f,k);loc=render_audio(p)
        text=t['refined_text'];self.assertNotIn('嗯',text);self.assertNotIn('三十',text);self.assertNotIn('不对',text)
        self.assertEqual(text.count('支持'),1);self.assertIn('不是四十万',text);self.assertIn('Kimi',text);self.assertIn('很很重要',text)
        verify_splice(p,t,loc/'narration.wav')
        for w in t['words']:
            self.assertEqual(w['end_sample']-w['start_sample'],w['source_end_sample']-w['source_start_sample'])
        self.assertEqual(render_audio(p),loc) # safe retry returns the exact verified artifact
    def test_03_protected_negation_numbers_names_require_explicit_reason(self):
        for idx in (9,10,12):
            with self.subTest(idx=idx):
                p,k=self.draft() if not self.out.exists() else (self.out/'project',None)
                original=read(p/'manuscript.json');d=copy.deepcopy(original);d['decisions'][idx].update(action='delete',category='mistake');wid=d['decisions'][idx]['id'];d['order'].remove(wid);d.pop('caption_groups',None);write(p/'manuscript.json',d)
                with self.assertRaisesRegex(ValueError,'Protected'):compile_edit(p)
                write(p/'manuscript.json',original)
    def test_04_reorder_maps_words_and_samples_in_output_order(self):
        p,k=self.draft();d=read(p/'manuscript.json');d['order']=d['order'][-3:]+d['order'][:-3];d['caption_groups']=[[i] for i in d['order']];write(p/'manuscript.json',d)
        with self.assertRaisesRegex(ValueError,'Reordering'):compile_edit(p)
        d['reorder_reason']='Explicit fixture rearrangement, subject to human review';write(p/'manuscript.json',d);t=compile_edit(p)
        self.assertTrue(t['reordered']);self.assertEqual([w['id'] for w in t['words']],d['order']);self.assertEqual(sorted(w['start_sample'] for w in t['words']),[w['start_sample'] for w in t['words']])
    def test_05_word_boundary_and_srt_precision(self):
        p,k=self.draft();t=compile_edit(p)
        self.assertEqual(t['output_samples'],sum(s['source_end_sample']-s['source_start_sample'] for s in t['segments']))
        for c in t['captions']:self.assertGreaterEqual(round(c['start']*1000),0);self.assertLessEqual(round(c['end']*1000),round(t['duration_seconds']*1000))
        d=read(p/'manuscript.json');d['pause_deletions'][0]['start']=.16;write(p/'manuscript.json',d)
        with self.assertRaisesRegex(ValueError,'overlaps speech'):compile_edit(p)
    def test_06_model_boolean_cannot_approve_and_wrong_signer_rejected(self):
        p,k=self.draft();q,f,t=manuscript_request(p);write(f/'approval.json',{'approved':True,'approved_by':'agent'})
        with self.assertRaisesRegex(ValueError,'forged|missing'):render_audio(p)
        other=example.crypto('generate',{'passphrase':'other-synthetic-key'});write(f/'approval.json',issue(q,other['private_key'],'other-synthetic-key'))
        with self.assertRaisesRegex(ValueError,'trusted human'):render_audio(p)
    def test_07_script_approval_is_a_second_independent_gate(self):
        p,plan=self.complete();q,f,_,_=director_request(plan);saved=read(f/'approval.json');(f/'approval.json').unlink()
        with self.assertRaisesRegex(ApprovalRequired,'video script'):assert_director(plan)
        # A manuscript receipt cannot satisfy the director stage.
        mq,mf,_=manuscript_request(p);write(f/'approval.json',read(mf/'approval.json'))
        with self.assertRaisesRegex(ValueError,'stale|mismatch'):assert_director(plan)
        write(f/'approval.json',saved);assert_director(plan)
    def test_08_edit_invalidates_both_approvals_and_revert_cannot_reuse_old_generation(self):
        p,plan=self.complete();original=read(p/'manuscript.json');changed=copy.deepcopy(original);changed['revision']=2;changed['decisions'][1]['reason']='Revised retention rationale';write(p/'manuscript.json',changed)
        with self.assertRaisesRegex(ValueError,'stale'):assert_director(plan)
        # Even restoring the old files after a failed/stale check cannot resurrect the old generation.
        write(p/'manuscript.json',original)
        with self.assertRaises(ApprovalRequired):render_audio(p)
    def test_09_director_script_asset_and_plan_changes_invalidate_receipt(self):
        p,plan=self.complete();script=Path(read(plan)['workflow']['director_script']);script.write_text(script.read_text()+'\nChanged visual direction')
        with self.assertRaises(ApprovalRequired):assert_director(plan)
    def test_10_source_material_hash_mutation_blocks_retry(self):
        p,plan=self.complete();source=Path(read(p/'source.json')['source']);source.write_bytes(source.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash changed'):assert_director(plan)
    def test_11_forged_preparation_report_cannot_substitute_audio_or_subtitles(self):
        p,plan=self.complete();loc=render_audio(p);f=loc/'narration.wav';b=bytearray(f.read_bytes());b[-100]^=1;f.write_bytes(b)
        report=read(loc/'audio-preparation-report.json');report['audio_sha256']=sha(f);write(loc/'audio-preparation-report.json',report)
        with self.assertRaisesRegex(ValueError,'original-voice splice'):assert_director(plan)
    def test_12_legacy_approved_flags_cannot_enter_production(self):
        f=Path(self.temp.name)/'legacy.json';write(f,{'status':'approved','approved':True,'example_only':True})
        with self.assertRaisesRegex(ValueError,'Legacy'):assert_director(f)
        r=subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(f),'--project-dir',str(Path(self.temp.name)/'composition')],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('migration',r.stderr)
    def test_13_sealed_review_tampering_blocks_user_signing(self):
        p,k=self.draft();q,f,t=manuscript_request(p);(f/'review.md').write_text('Different manuscript')
        with self.assertRaisesRegex(ValueError,'Sealed'):manuscript_request(p)
    def test_14_semantic_evidence_cannot_be_copied_to_new_draft(self):
        p,k=self.draft();d=read(p/'manuscript.json');d['decisions'][1]['reason']='new draft';write(p/'manuscript.json',d)
        with self.assertRaisesRegex(ValueError,'stale'):manuscript_request(p)
    def test_15_production_source_cannot_claim_fixture_approval(self):
        p,k=self.draft();m=read(p/'source.json');m['example_only']=False;write(p/'source.json',m)
        pr=preview(p);e=read(p/'semantic-review.json');e.update(manuscript_digest=manuscript_base(p),preview_sha256=pr['audio_sha256']);write(p/'semantic-review.json',e)
        with self.assertRaisesRegex(ValueError,'production'):manuscript_request(p)
    def test_16_complete_initialization_keeps_exact_approved_assets(self):
        p,plan=self.complete();r=subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(plan),'--project-dir',str(p/'hyperframes')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);assert_director(plan,p/'hyperframes')
        self.assertNotIn('<video',(p/'hyperframes/index.html').read_text())
    def test_17_presenter_audio_video_share_sample_timeline(self):
        p,k=self.draft();q,f,t=manuscript_request(p);example.approve_fixture(q,f,k);loc=render_audio(p)
        m=read(p/'source.json');original=Path(m['source']);video=Path(self.temp.name)/'source.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x90:rate=30','-i',str(original),'-map','0:v','-map','1:a','-c:v','libx264','-c:a','aac','-shortest','-y',str(video)],check=True)
        # A/V integration test uses synthetic footage; fixture production authority rejects arbitrary video.
        m.update(source=str(video),source_sha256=sha(video),has_video=True);write(p/'source.json',m)
        result=render_presenter(p,t,loc/'narration.wav',Path(self.temp.name)/'edited.mp4');self.assertEqual(result['fps'],30)
        from spoken_edit import probe
        info=probe(result['path']);streams={s['codec_type']:s for s in info['streams']}
        self.assertLessEqual(abs(float(streams['video']['duration'])-float(streams['audio']['duration'])),2/30)
    def test_18_caption_only_rewrite_cannot_remove_a_protected_negation(self):
        p,k=self.draft();d=read(p/'manuscript.json');d['corrections']['w00009']={'text':'是','reason':'Claimed ASR change','listening_evidence':'fixture'};write(p/'manuscript.json',d)
        with self.assertRaisesRegex(ValueError,'Protected ASR'):compile_edit(p)
    def test_19_director_material_changes_invalidate_approval(self):
        p,plan=self.complete();d=read(plan);asset=p/'material.txt';asset.write_text('original');d['assets']=[str(asset)];write(plan,d)
        with self.assertRaises(ApprovalRequired):assert_director(plan)
        q,f,_,_=director_request(plan)
        # Even without a new signature, material hash change produces a different request.
        asset.write_text('changed');other,_,_,_=director_request(plan);self.assertNotEqual(q['subject'],other['subject'])
    def test_20_composition_audio_substitution_is_blocked(self):
        p,plan=self.complete();subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(plan),'--project-dir',str(p/'hyperframes')],check=True,capture_output=True)
        f=p/'hyperframes/assets/narration.wav';b=bytearray(f.read_bytes());b[-30]^=1;f.write_bytes(b)
        with self.assertRaisesRegex(ValueError,'Composition audio'):assert_director(plan,p/'hyperframes')
    def test_21_signature_tampering_and_noninteractive_self_approval_fail(self):
        p,k=self.draft();q,f,t=manuscript_request(p);example.approve_fixture(q,f,k);a=read(f/'approval.json');a['payload']['issued_at']='changed';write(f/'approval.json',a)
        with self.assertRaisesRegex(ValueError,'signature'):render_audio(p)
        r=subprocess.run([sys.executable,str(ROOT/'scripts/review_approval.py'),'approve','--request',str(f/'request.json')],input='APPROVE anything\n',capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('interactive terminal',r.stderr)
    def test_22_duplicate_or_omitted_word_cannot_silently_change_audio(self):
        p,k=self.draft();original=read(p/'manuscript.json')
        for order in [original['order'][:-1],original['order']+[original['order'][0]]]:
            d=copy.deepcopy(original);d['order']=order;write(p/'manuscript.json',d)
            with self.assertRaisesRegex(ValueError,'every retained word'):compile_edit(p)
    def test_23_example_tag_cannot_authorize_arbitrary_pcm(self):
        p,k=self.draft();m=read(p/'source.json');audio=p/'normalized-source.wav';b=bytearray(audio.read_bytes());b[-100]^=1;audio.write_bytes(b);m['normalized_sha256']=sha(audio);write(p/'source.json',m)
        with self.assertRaisesRegex(ValueError,'known synthetic'):__import__('spoken_workflow').project_trust(p)
    def test_24_final_aac_waveform_matches_edited_audio_and_rejects_raw(self):
        p,k=self.draft();q,f,t=manuscript_request(p);example.approve_fixture(q,f,k);loc=render_audio(p);aac=Path(self.temp.name)/'edited.m4a'
        subprocess.run(['ffmpeg','-v','error','-i',str(loc/'narration.wav'),'-c:a','aac','-b:a','192k',str(aac)],check=True)
        from verify_output_audio import compare_audio
        self.assertGreater(compare_audio(loc/'narration.wav',aac)['cosine'],.97)
        with self.assertRaisesRegex(ValueError,'duration|timeline'):compare_audio(Path(read(p/'source.json')['source']),aac)

    def test_25_stereo_clone_preserves_voice_and_actual_gain_change_is_rejected(self):
        p,k=self.draft();q,f,t=manuscript_request(p);example.approve_fixture(q,f,k);loc=render_audio(p)
        from verify_output_audio import compare_audio
        stereo=Path(self.temp.name)/'stereo.m4a';loud=Path(self.temp.name)/'loud.m4a'
        subprocess.run(['ffmpeg','-v','error','-i',str(loc/'narration.wav'),'-af','pan=stereo|c0=c0|c1=c0','-c:a','aac','-b:a','192k',str(stereo)],check=True)
        self.assertGreater(compare_audio(loc/'narration.wav',stereo)['cosine'],.97)
        subprocess.run(['ffmpeg','-v','error','-i',str(loc/'narration.wav'),'-af','volume=1.5','-c:a','aac','-b:a','192k',str(loud)],check=True)
        with self.assertRaisesRegex(ValueError,'does not match'):compare_audio(loc/'narration.wav',loud)

    def test_26_composition_subtitle_only_edit_is_rejected(self):
        p,plan=self.complete();subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(plan),'--project-dir',str(p/'hyperframes')],check=True,capture_output=True)
        html=p/'hyperframes/index.html';html.write_text(html.read_text().replace('个用户不是','个用户是'))
        with self.assertRaisesRegex(ValueError,'caption text'):assert_director(plan,p/'hyperframes')

    def test_27_missing_manuscript_evidence_blocks_with_actionable_message(self):
        p,k=self.draft();(p/'semantic-review.json').unlink()
        with self.assertRaisesRegex(ValueError,'Complete full manuscript review'):manuscript_request(p)
        self.assertFalse((p/'prepared').exists())
        self.assertFalse(list(p.glob('reviews/**/request.json')))

    def test_28_text_review_outputs_full_package_without_listening(self):
        p,k=self.draft();e=read(p/'semantic-review.json')
        e.update(mode='text-review',hearing='not-tested',source_listened_seconds=0,preview_listened_seconds=0,
                 review_disclosure='Full source and refined manuscripts reviewed; no listening required.',
                 findings='Every word decision and output caption checked against the source transcript.')
        write(p/'semantic-review.json',e)
        q,f,t=manuscript_request(p)
        self.assertEqual((f/'subtitle-review.srt').read_text(),t['srt'])
        self.assertIn('text-review',(f/'review.md').read_text())
        with self.assertRaises(ApprovalRequired):render_audio(p)
        self.assertFalse((p/'prepared').exists())

    def test_29_text_review_requires_disclosure_and_all_words(self):
        p,k=self.draft();e=read(p/'semantic-review.json')
        e.update(mode='text-review',hearing='not-tested',source_listened_seconds=0,preview_listened_seconds=0)
        write(p/'semantic-review.json',e)
        with self.assertRaisesRegex(ValueError,'Disclose'):manuscript_request(p)
        e['review_disclosure']='Full text review without listening';e['reviewed_word_ids']=e['reviewed_word_ids'][:-1]
        write(p/'semantic-review.json',e)
        with self.assertRaisesRegex(ValueError,'every source word'):manuscript_request(p)

    def test_30_asr_correction_accepts_documented_non_listening_evidence(self):
        p,k=self.draft();d=read(p/'manuscript.json')
        d['corrections']['w00009']={'text':'不是','reason':'Textual confirmation',
                                  'evidence':'Owner explicitly confirmed the wording; hearing not tested.'}
        write(p/'manuscript.json',d)
        self.assertIn('不是',compile_edit(p)['refined_text'])

    def test_31_same_model_asr_without_listening_retains_proxy_binding(self):
        p,k=self.draft();v=read(p/'preview.json');e=read(p/'semantic-review.json')
        path=p/'proxy-asr.json';write(path,{'source':v['audio'],'duration_seconds':v['duration_seconds'],
                                         'segments':[{'text':'fixture transcript'}]})
        e.update(mode='same-model-asr',hearing='not-tested',source_listened_seconds=0,preview_listened_seconds=0,
                 review_disclosure='ASR and complete text reviewed, without listening.',asr_transcript=str(path),
                 asr_sha256=sha(path),source_model='fixture-asr',review_model='fixture-asr')
        write(p/'semantic-review.json',e);manuscript_request(p)
        raw=read(path);raw['source']='another.wav';write(path,raw);e['asr_sha256']=sha(path);write(p/'semantic-review.json',e)
        with self.assertRaisesRegex(ValueError,'does not match'):manuscript_request(p)

    def test_32_text_review_cannot_claim_unperformed_listening(self):
        p,k=self.draft();e=read(p/'semantic-review.json')
        e.update(mode='text-review',hearing='not-tested',source_listened_seconds=1,preview_listened_seconds=0,
                 review_disclosure='Text only.')
        write(p/'semantic-review.json',e)
        with self.assertRaisesRegex(ValueError,'zero listened seconds'):manuscript_request(p)

if __name__=='__main__':unittest.main()
