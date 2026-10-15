#!/usr/bin/env python3
"""Local, deterministic two-approval fixture. No human identity, private input or API."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from example_fixture import fixture
from spoken_edit import initialize,read,write,source_state,sha
from spoken_workflow import preview,manuscript_base,manuscript_request,render_audio,director_request,assert_director
from review_approval import crypto,issue

def draft_example(out):
    out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new empty example directory')
    out.mkdir(parents=True,exist_ok=True);audio,t,_=fixture();(out/'source.wav').write_bytes(audio);write(out/'source-transcript.json',t)
    p=out/'project';initialize(out/'source.wav',out/'source-transcript.json',p,example_only=True)
    keys=crypto('generate',{'passphrase':'public-synthetic-fixture-only'});(p/'example-public.pem').write_text(keys['public_key'])
    d=read(p/'manuscript.json')
    for i,category in [(0,'filler'),(2,'redundant_repeat'),(4,'correction'),(5,'correction')]:
        d['decisions'][i].update(action='delete',category=category,reason='Authored fixture: '+('keep the later corrected forty' if i in (4,5) else 'remove a nonsemantic filler / failed first repetition'))
        if i in (4,5):d['decisions'][i]['sensitive_change_reason']='Explicit correction: 三十，不对，四十; retain 四十 and the later 不是四十万 negation.'
    d['decisions'][9]['reason']='Retain negation 不是: it changes the meaning.'
    for i in (13,14):d['decisions'][i]['reason']='Retain intentional repeated emphasis 很很.'
    d['order']=[x['id'] for x in d['decisions'] if x['action']=='keep'];d['reviewed_word_ids']=[x['id'] for x in d['decisions']]
    ws=t['segments'][0]['words'];d['pause_deletions']=[{'start':ws[8]['end']+.11,'end':ws[9]['start']-.11,'reason':'Authored long silent interval; retain both sides of the pause.'}]
    d['protected_terms']=['Kimi'];d['caption_groups']=[d['order'][i:i+3] for i in range(0,len(d['order']),3)];write(p/'manuscript.json',d)
    proxy=preview(p)
    write(p/'semantic-review.json',{'mode':'synthetic','manuscript_digest':manuscript_base(p),'preview_sha256':proxy['audio_sha256'],
          'reviewed_word_ids':d['reviewed_word_ids'],'source_listened_seconds':proxy['source_duration_seconds'],
          'preview_listened_seconds':proxy['duration_seconds'],'findings':'Synthetic fixture coverage only: tones and authored transcript, not real listening or live ASR. Negation, number, name and deliberate repetition retained.'})
    return p,keys

def approve_fixture(request,folder,keys):
    if not request.get('example_only'):raise ValueError('Fixture signer never signs production requests')
    write(folder/'approval.json',issue(request,keys['private_key'],'public-synthetic-fixture-only'))

def complete_example(out):
    p,keys=draft_example(out);q,f,_=manuscript_request(p);approve_fixture(q,f,keys);loc=render_audio(p)
    d=read(loc/'audio-preparation-report.json');duration=d['duration_seconds'];fps=30;end=round(duration*fps);a=end//3;b=2*end//3
    script=p/'MG导演脚本.md';script.write_text('# 合成示例视频脚本\n\n1. 显示修正后的“四十个用户”，依次展开数量与对象。\n2. 同屏比较“四十个”和“四十万”，突出保留的“不是”。\n3. 用连接线与高亮解释 Kimi 的强调语气。\n\n此例使用按词标记的音调而非真人录音，不代表真实 ASR 或听感验收。\n')
    plan=read(ROOT/'examples/plan-validation/plan.json');plan['source']={'audio':str(loc/'narration.wav'),'subtitles':str(loc/'final.srt'),'duration_seconds':duration}
    plan['workflow']={'schema':'draftcut.workflow.v2','project_dir':str(p),'director_script':str(script)}
    plan['cues']=[{'id':'quantity','start_seconds':0,'end_seconds':a/fps,'visual_prompt':'逐步呈现四十个用户，用图形解释数量。'},
                  {'id':'negation','start_seconds':a/fps,'end_seconds':b/fps,'visual_prompt':'对比40与400000，高亮保留的否定。'},
                  {'id':'emphasis','start_seconds':b/fps,'end_seconds':end/fps,'visual_prompt':'用连接线与重点文字展示保留的强调。'}]
    path=p/'director-plan.json';write(path,plan);q,f,_,_=director_request(path);approve_fixture(q,f,keys);assert_director(path)
    return p,path

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output-dir',type=Path,required=True);a.add_argument('--initialize-composition',action='store_true');args=a.parse_args()
    p,plan=complete_example(args.output_dir)
    if args.initialize_composition:subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(plan),'--project-dir',str(p/'hyperframes')],check=True)
    print(json.dumps({'scope':'synthetic fixture, no real human approvals','project':str(p),'plan':str(plan),'prepared':str(render_audio(p))},ensure_ascii=False))
if __name__=='__main__':main()
