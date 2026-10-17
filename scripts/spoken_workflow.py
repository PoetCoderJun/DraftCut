#!/usr/bin/env python3
"""Two human approvals bound to source, word decisions, audio, script and assets."""
from __future__ import annotations
import argparse, contextlib, hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from spoken_edit import initialize,source_state,compile_edit,splice,render_presenter,read,write,sha,SR,verify_splice
from review_approval import canonical,digest,verify_receipt,TRUST_FILE

class ApprovalRequired(ValueError):pass

def verify_stage(p,request,receipt):
    m,_,_=source_state(p)
    if m.get('simulation_run'):
        from simulation import context,verify
        run,public=context(p,m)
        if request.get('simulation_run')!=m['simulation_run']:raise ValueError('Review simulation scope mismatch')
        return verify(request,receipt,run,public)
    if request.get('simulation_run'):raise ValueError('Simulation receipt cannot authorize production')
    return verify_receipt(request,receipt,project_trust(p))

def record_capabilities(p,audio_input,reason):
    timeline=compile_edit(p);proxy=read(p/'preview.json');m,_,words=source_state(p)
    result={'audio_input':audio_input,'reason':reason,'hearing':'not-tested' if audio_input=='unavailable' else 'pending',
            'manuscript_digest':manuscript_base(p),'preview_sha256':proxy['audio_sha256']}
    write(p/'capabilities.json',result)
    if m.get('simulation_run'):
        from simulation import context
        run,_=context(p,m)
        write(p/'semantic-review.json',{'mode':'simulation','run_id':run['run_id'],'scope':'usability-test-only',
              **result,'reviewed_word_ids':[w['id'] for w in words],'source_listened_seconds':0,'preview_listened_seconds':0,
              'findings':'Full transcript and sample mapping checked for interaction testing; listening quality is not assessed.'})
    return result

def project_trust(p):
    m,t,_=source_state(p)
    if m.get('example_only'):
        from example_fixture import assert_fixture
        assert_fixture(p,m,t)
        return (p/'example-public.pem').read_text()
    if not TRUST_FILE.is_file():raise ApprovalRequired('Human reviewer is not configured. Run review_approval.py setup yourself, outside the Agent, before approving a production request')
    if TRUST_FILE.resolve().is_relative_to(p.resolve()):raise ValueError('Production trust must live outside the editable project')
    return TRUST_FILE.read_text()

def manuscript_base(p):
    m,_,_=source_state(p)
    return digest({'source_manifest':m,'manuscript':read(p/'manuscript.json')})

def preview(p):
    timeline=compile_edit(p);base=manuscript_base(p);folder=p/'previews'/base[:20];folder.mkdir(parents=True,exist_ok=True)
    audio=folder/'REVIEW-ONLY.wav'
    if not audio.exists():info=splice(p,timeline,audio);write(folder/'audio.json',info)
    else:
        info=read(folder/'audio.json')
        if sha(audio)!=info['audio_sha256']:raise ValueError('Review proxy was altered; preserve evidence and create a revised draft')
    write(folder/'timeline.json',timeline)
    result={'schema':'draftcut.review-proxy.v2','manuscript_digest':base,'audio':str(audio),'audio_sha256':sha(audio),'timeline_sha256':sha(folder/'timeline.json'),
            'duration_seconds':timeline['duration_seconds'],'source_duration_seconds':timeline['source_samples']/SR,'purpose':'review-only; never an approved production master'}
    write(p/'preview.json',result)
    return result

def semantic_evidence(p,timeline):
    proxy=read(p/'preview.json');base=manuscript_base(p)
    if proxy.get('manuscript_digest')!=base or sha(proxy['audio'])!=proxy['audio_sha256']:raise ValueError('Semantic review proxy is missing/stale; regenerate and review the full manuscript again')
    verify_splice(p,timeline,proxy['audio'])
    evidence_path=p/'semantic-review.json'
    if not evidence_path.is_file():raise ValueError('Complete full manuscript review before requesting manuscript approval; record text-review or ASR evidence in '+str(evidence_path))
    e=read(evidence_path)
    if e.get('manuscript_digest')!=base or e.get('preview_sha256')!=proxy['audio_sha256']:raise ValueError('Semantic review evidence is stale')
    mode=e.get('mode');m,_,words=source_state(p)
    if set(e.get('reviewed_word_ids',[]))!={w['id'] for w in words}:raise ValueError('Semantic review must cover every source word, not just mechanical candidates')
    if mode=='simulation':
        from simulation import context
        scoped=context(p,m)
        if not scoped or e.get('run_id')!=scoped[0]['run_id'] or e.get('scope')!='usability-test-only' or e.get('hearing')!='not-tested':
            raise ValueError('Simulation evidence cannot substitute for production review')
        if e.get('source_listened_seconds')!=0 or e.get('preview_listened_seconds')!=0:raise ValueError('Do not invent listening in a simulation')
    elif mode=='text-review' or (mode=='same-model-asr' and e.get('hearing')=='not-tested'):
        if e.get('hearing')!='not-tested' or any(e.get(field)!=0 for field in ('source_listened_seconds','preview_listened_seconds')):
            raise ValueError('Text-only review must honestly record hearing=not-tested and zero listened seconds')
        if not str(e.get('review_disclosure','')).strip():raise ValueError('Disclose full text review and the absence of listening')
    elif mode=='human-listening' or mode=='synthetic' or mode=='same-model-asr':
        for field,expected in [('source_listened_seconds',timeline['source_samples']/SR),('preview_listened_seconds',timeline['duration_seconds'])]:
            if abs(float(e.get(field,-1))-expected)>.001:raise ValueError('Record actual complete source and proxy listening before requesting approval')
    if not str(e.get('findings','')).strip():raise ValueError('Record full manuscript findings and unresolved wording')
    if mode=='same-model-asr':
        path=Path(e['asr_transcript']);asr=read(path)
        if sha(path)!=e.get('asr_sha256') or str(Path(asr.get('source','')).resolve())!=str(Path(proxy['audio']).resolve()):raise ValueError('Semantic ASR does not match the reviewed proxy')
        if not e.get('source_model') or e['source_model']!=e.get('review_model'):raise ValueError('Semantic ASR must use the source model')
        if abs(float(asr.get('duration_seconds',0))-timeline['duration_seconds'])>.1:raise ValueError('Semantic ASR has the wrong duration')
        if not asr.get('segments'):raise ValueError('Semantic ASR transcript is empty')
    elif mode=='text-review':pass
    elif mode=='human-listening':
        if not str(e.get('offline_review_disclosure','')).strip():raise ValueError('Disclose the complete listening alternative to cloud re-ASR in the review')
    elif mode=='simulation':pass
    elif mode=='synthetic':
        if not m.get('example_only'):raise ValueError('Synthetic semantic evidence cannot approve a production project')
        project_trust(p)
    else:raise ValueError('Use text-review, same-model-asr, optional human-listening, or the restricted synthetic fixture')
    return e,proxy

def sync(p,subject):
    state_path=p/'workflow-state.json';s=read(state_path) if state_path.exists() else {'schema':'draftcut.workflow.v2','generation':0,'director_generation':0}
    if s.get('active_subject')!=subject:
        s.update(generation=s['generation']+1,active_subject=subject,active_director=None)
        write(state_path,s)
    return s

def observe_inputs(p):
    """Burn approvals on every observed edit, including invalid/intermediate drafts."""
    files=[p/'source.json',p/'manuscript.json',p/'semantic-review.json',p/'preview.json',p/'transcript.json',p/'normalized-source.wav']
    try:
        m=read(p/'source.json');files.extend([Path(m['source']),Path(m['original_transcript'])])
        if (p/'preview.json').exists():files.append(Path(read(p/'preview.json')['audio']))
    except (KeyError,ValueError,OSError):pass
    fingerprint=digest([{'path':str(f),'sha256':sha(f) if f.is_file() else None} for f in files])
    return sync(p,fingerprint)

def immutable(path,value):
    content=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if path.exists():
        if path.read_text()!=content:raise ValueError('Sealed review artifact changed: '+str(path))
    else:path.write_text(content)

def manuscript_request(p):
    p=Path(p).resolve()
    state=observe_inputs(p)
    timeline=compile_edit(p);e,proxy=semantic_evidence(p,timeline);m,_,words=source_state(p);d=read(p/'manuscript.json')
    subject=digest({'base':manuscript_base(p),'semantic_evidence':e,'proxy':proxy})
    folder=p/'reviews'/f'manuscript-g{state["generation"]}-{subject[:12]}';folder.mkdir(parents=True,exist_ok=True)
    by_id={x['id']:x for x in d['decisions']}
    lines=['# 口播稿审核 / Spoken manuscript review',f'\nProject: {m["project_id"]} · revision {d["revision"]} · generation {state["generation"]}',
           '\n## 原始口播 / Before\n'+timeline['source_text'],'\n## 精炼口播 / After\n'+timeline['refined_text'],
           '\n## 逐词差异与依据 / Every source word', '| ID | 原词 | 决定 | 分类 | 依据 |','| --- | --- | --- | --- | --- |']
    if m.get('simulation_run'):lines.insert(1,'\nSIMULATED USER TEST · owner_approval=false · hearing=not-tested. This is an interaction test, not a quality acceptance.')
    def cell(x):return str(x).replace('|','\\|').replace('\n',' ')
    for w in words:
        x=by_id[w['id']];reason=x['reason']
        if x.get('sensitive_change_reason'):reason+=' · SENSITIVE: '+x['sensitive_change_reason']
        lines.append('| '+' | '.join(map(cell,[w['id'],w['text'],x['action'],x['category'],reason]))+' |')
    lines+=['\n## 改口、纠错、移序与停顿 / Additional changes',canonical({'corrections':d.get('corrections',{}),'order':d['order'],'reorder_reason':d.get('reorder_reason',''),'pause_deletions':d.get('pause_deletions',[])}),
            '\n## 文稿复核方式 / Manuscript review method',str(proxy['audio']),canonical(e),'\n## 完整字幕 / Complete output-timed subtitles\n```srt\n'+timeline['srt']+'```',
            '\n签名确认此素材、此稿件、此时间线和披露的语义复核方式。只有确认后才生成正式精炼音频；没有 TTS 补词。 / Approve only after reviewing the exact manuscript, edits, subtitles and disclosed review method; listening is optional.']
    review='\n'.join(lines)+'\n';immutable(folder/'review.md',review);immutable(folder/'subtitle-review.srt',timeline['srt']);immutable(folder/'timeline.json',timeline)
    request={'schema':'draftcut.review-request.v2','stage':'manuscript','project_id':m['project_id'],'project_dir':str(p.resolve()),'generation':state['generation'],
             'subject':subject,'review_sha256':sha(folder/'review.md'),'subtitle_sha256':sha(folder/'subtitle-review.srt'),'timeline_sha256':sha(folder/'timeline.json'),
             'example_only':m['example_only']}
    if m.get('simulation_run'):
        request['simulation_run']=m['simulation_run']
    immutable(folder/'request.json',request)
    return request,folder,timeline

def approved_manuscript(p):
    request,folder,t=manuscript_request(p)
    receipt=folder/'approval.json'
    if not receipt.is_file():raise ApprovalRequired('Awaiting explicit human approval of the current spoken manuscript: '+str(folder/'request.json'))
    receipt_hash=verify_stage(p,request,read(receipt))
    return request,folder,t,receipt_hash

def check_prepared(p):
    req,folder,t,receipt=approved_manuscript(p);state=read(p/'workflow-state.json')
    loc=p/'prepared'/f'g{req["generation"]}-{receipt[:12]}'
    report=read(loc/'audio-preparation-report.json')
    if report.get('manuscript_request_sha256')!=digest(req) or report.get('approval_sha256')!=receipt:raise ValueError('Prepared audio belongs to a different approval')
    for key in ('audio','subtitles','transcript'):
        file=loc/report[key]
        if not file.is_file() or sha(file)!=report[key+'_sha256']:raise ValueError('Approved prepared artifact changed: '+key)
    verify_splice(p,t,loc/'narration.wav')
    if (loc/'final.srt').read_text()!=t['srt']:raise ValueError('Subtitles differ from the approved spoken words')
    refined=read(loc/'transcript.json')
    if refined.get('words')!=t['words'] or refined.get('segments')!=t['captions']:raise ValueError('Refined word mapping changed')
    if report.get('presenter'):
        file=Path(report['presenter']['path'])
        if sha(file)!=report['presenter']['sha256']:raise ValueError('Edited presenter changed')
    return loc,report,t

def render_audio(p):
    req,folder,t,receipt=approved_manuscript(p);loc=p/'prepared'/f'g{req["generation"]}-{receipt[:12]}'
    if loc.exists():check_prepared(p);return loc
    (p/'prepared').mkdir(exist_ok=True);temp=Path(tempfile.mkdtemp(prefix='.building-',dir=p/'prepared'))
    try:
        info=splice(p,t,temp/'narration.wav');(temp/'final.srt').write_text(t['srt']);write(temp/'transcript.json',{'schema':'draftcut.refined-transcript.v2','duration_seconds':t['duration_seconds'],'words':t['words'],'segments':t['captions']})
        presenter=render_presenter(p,t,temp/'narration.wav',temp/'presenter.mp4') if read(p/'manuscript.json').get('include_presenter',False) else None
        if presenter:presenter['path']=str((loc/'presenter.mp4').resolve())
        report={'schema_version':'draftcut.audio-preparation.v2','manuscript_request_sha256':digest(req),'approval_sha256':receipt,
                'duration_seconds':t['duration_seconds'],'timeline':t,'pcm_check':info,'presenter':presenter}
        if req.get('simulation_run'):report.update(simulation_run=req['simulation_run'],owner_approval=False,hearing='not-tested')
        for key,file in [('audio','narration.wav'),('subtitles','final.srt'),('transcript','transcript.json')]:report[key]=file;report[key+'_sha256']=sha(temp/file)
        write(temp/'audio-preparation-report.json',report)
        # Recheck all source/draft/evidence hashes after processing, before committing the transaction.
        if digest(approved_manuscript(p)[0])!=digest(req):raise ValueError('Manuscript changed during audio rendering')
        temp.rename(loc)
    except BaseException:raise # Failed transaction is preserved for inspection; not accepted downstream.
    return loc

def director_request(plan_path,script_path=None):
    plan_path=Path(plan_path).resolve();plan=read(plan_path);w=plan.get('workflow',{})
    if w.get('schema')!='draftcut.workflow.v2' or not w.get('project_dir'):raise ValueError('Legacy/bool-approved plan: explicitly migrate and obtain both human approvals')
    p=Path(w['project_dir']).resolve();loc,prepared,t=check_prepared(p);m,_,_=source_state(p)
    script_path=Path(script_path or w.get('director_script','')).resolve()
    if str(Path(w.get('director_script','')).resolve())!=str(script_path):raise ValueError('Set workflow.director_script to the reviewed script path before requesting approval')
    state=read(p/'workflow-state.json')
    observed_assets=[]
    for raw in plan.get('assets',[]):
        file=(plan_path.parent/raw).resolve();observed_assets.append({'path':str(file),'sha256':sha(file) if file.is_file() else None})
    observed=digest({'plan_sha256':sha(plan_path),'script_sha256':sha(script_path) if script_path.is_file() else None,'assets':observed_assets,'manuscript_generation':state['generation']})
    if state.get('observed_director')!=observed:
        state.update(director_generation=state.get('director_generation',0)+1,observed_director=observed,active_director=None);write(p/'workflow-state.json',state)
    if not script_path.is_file() or not script_path.read_text().strip():raise ValueError('Video director script is required')
    for key,file in [('audio','narration.wav'),('subtitles','final.srt')]:
        if (plan_path.parent/plan['source'][key]).resolve()!=(loc/file).resolve():raise ValueError('Director plan must use the approved refined audio and matching SRT')
    if abs(float(plan['source']['duration_seconds'])-t['duration_seconds'])>1/SR:raise ValueError('Director duration differs from the approved sample timeline')
    if bool(plan.get('example_only'))!=bool(m['example_only']):raise ValueError('Example/production scope mismatch')
    assets=[]
    for raw in plan.get('assets',[]):
        file=(plan_path.parent/raw).resolve()
        if not file.is_file():raise ValueError('Director material is missing: '+str(file))
        assets.append({'path':str(file),'sha256':sha(file)})
    from validate_plan import validate
    errors=validate(plan)
    if errors:raise ValueError('; '.join(errors))
    state=read(p/'workflow-state.json');subject=digest({'plan_sha256':sha(plan_path),'script_sha256':sha(script_path),'prepared':prepared,'assets':assets,'manuscript_generation':state['generation']})
    if state.get('active_director')!=subject:
        state.update(active_director=subject);write(p/'workflow-state.json',state)
    folder=p/'reviews'/f'director-g{state["generation"]}-d{state["director_generation"]}-{subject[:12]}';folder.mkdir(parents=True,exist_ok=True)
    review='# 视频脚本审核 / Video director review\n\n'+script_path.read_text()+'\n\n## 批准音频与素材 / Approved audio and assets\n'+canonical({'prepared':str(loc),'audio_sha256':prepared['audio_sha256'],'assets':assets})+'\n\n## 完整结构化计划 / Complete machine plan\n```json\n'+json.dumps(plan,ensure_ascii=False,indent=2)+'\n```\n'
    if m.get('simulation_run'):review='SIMULATED USER TEST · owner_approval=false · hearing=not-tested\n\n'+review
    immutable(folder/'review.md',review)
    request={'schema':'draftcut.review-request.v2','stage':'director','project_id':m['project_id'],'project_dir':str(p),'generation':state['generation'],
             'director_generation':state['director_generation'],'plan_path':str(plan_path),'script_path':str(script_path),'subject':subject,
             'review_sha256':sha(folder/'review.md'),'example_only':m['example_only']}
    if m.get('simulation_run'):request['simulation_run']=m['simulation_run']
    immutable(folder/'request.json',request);return request,folder,loc,prepared

def assert_director(plan_path,project_dir=None):
    req,folder,loc,prepared=director_request(plan_path)
    receipt=folder/'approval.json'
    if not receipt.is_file():raise ApprovalRequired('Awaiting explicit human approval of this video script: '+str(folder/'request.json'))
    p=Path(req['project_dir']);approval=verify_stage(p,req,read(receipt))
    if project_dir:
        project_dir=Path(project_dir)
        if project_dir.resolve()!=(p/'hyperframes').resolve():raise ValueError('Composition must belong to the approved workflow project')
        for a,b in [(project_dir/'assets/narration.wav',loc/'narration.wav'),(project_dir/'final.srt',loc/'final.srt')]:
            if not a.is_file() or sha(a)!=sha(b):raise ValueError('Composition audio/subtitle asset differs from the approved master')
        from composition_contract import check_composition
        check_composition(project_dir,compile_edit(p))
        if req.get('simulation_run') and 'id="draftcut-test-watermark"' not in (project_dir/'index.html').read_text():raise ValueError('Simulation export requires its permanent test watermark')
    return {'status':'approved','manuscript_generation':req['generation'],'director_request_sha256':digest(req),'director_approval_sha256':approval,
            'audio_sha256':prepared['audio_sha256'],'subtitles_sha256':prepared['subtitles_sha256'],'example_only':req['example_only'],
            **({'simulation_run':{**req['simulation_run'],'run_root':str(Path(req['simulation_run']['manifest']).parent)},'owner_approval':False,'hearing':'not-tested'} if req.get('simulation_run') else {})}

def validate_request(request,path):
    p=Path(request['project_dir'])
    if request['stage']=='manuscript':current,folder,_=manuscript_request(p)
    else:current,folder,_,_=director_request(request['plan_path'],request['script_path'])
    if current!=request or (folder/'request.json').resolve()!=Path(path).resolve():raise ValueError('Approval request is stale or not the current sealed review')

@contextlib.contextmanager
def locked(p):
    import fcntl
    p=Path(p)
    if not (p/'source.json').is_file():raise ValueError('Workflow project is missing; import the source into a new project first')
    with (p/'.workflow.lock').open('a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another workflow transaction is running for this project')
        yield

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    a=sub.add_parser('init');a.add_argument('--source',type=Path,required=True);a.add_argument('--transcript',type=Path,required=True);a.add_argument('--project-dir',type=Path,required=True);a.add_argument('--example',action='store_true');a.add_argument('--simulation-run',type=Path)
    a=sub.add_parser('record-capabilities');a.add_argument('--project-dir',type=Path,required=True);a.add_argument('--audio-input',choices=['available','unavailable'],required=True);a.add_argument('--reason',required=True)
    a=sub.add_parser('migrate');a.add_argument('--legacy-plan',type=Path,required=True);a.add_argument('--source',type=Path,required=True);a.add_argument('--transcript',type=Path,required=True);a.add_argument('--project-dir',type=Path,required=True)
    for name in ('preview','manuscript-review','render-audio'):
        a=sub.add_parser(name);a.add_argument('--project-dir',type=Path,required=True)
    a=sub.add_parser('director-review');a.add_argument('--plan',type=Path,required=True);a.add_argument('--script',type=Path)
    a=sub.add_parser('check');a.add_argument('--plan',type=Path,required=True);a.add_argument('--composition',type=Path)
    args=ap.parse_args()
    if args.command=='migrate':
        legacy=read(args.legacy_plan)
        result=initialize(args.source,args.transcript,args.project_dir)
        write(args.project_dir/'legacy-import.json',{'legacy_plan':str(args.legacy_plan.resolve()),'legacy_sha256':sha(args.legacy_plan),'inherited_approvals':False,'status':'needs_new_manuscript_and_director_approvals'})
    elif args.command=='init':
        result=initialize(args.source,args.transcript,args.project_dir,example_only=args.example)
        if args.simulation_run:
            if args.example:raise ValueError('Simulation and synthetic fixture scopes are distinct')
            from simulation import attach
            result=attach(args.project_dir,result,args.simulation_run);write(args.project_dir/'source.json',result)
        if args.example:
            from example_fixture import assert_fixture
            m,t,_=source_state(args.project_dir);assert_fixture(args.project_dir,m,t)
    elif args.command in ('director-review','check'):
        p=Path(read(args.plan).get('workflow',{}).get('project_dir',''))
        if not str(p) or str(p)=='.':raise ValueError('Legacy project requires explicit migration')
        with locked(p):
            if args.command=='check':result=assert_director(args.plan,args.composition)
            else:q,folder,_,_=director_request(args.plan,args.script);result={'request':str(folder/'request.json'),'review':str(folder/'review.md')}
    else:
        p=args.project_dir.resolve()
        with locked(p):
            if args.command=='preview':result=preview(p)
            elif args.command=='record-capabilities':result=record_capabilities(p,args.audio_input,args.reason)
            elif args.command=='manuscript-review':q,f,_=manuscript_request(p);result={'request':str(f/'request.json'),'review':str(f/'review.md'),'status':'awaiting_human_approval'}
            else:result={'prepared':str(render_audio(p))}
    print(json.dumps(result,ensure_ascii=False,default=str))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,TypeError,subprocess.CalledProcessError) as error:print(str(error),file=sys.stderr);raise SystemExit(1)
