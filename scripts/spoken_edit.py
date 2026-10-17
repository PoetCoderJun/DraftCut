#!/usr/bin/env python3
"""Word-accounted original-voice editing, using clean-talking's conservative candidates."""
from __future__ import annotations
import copy, hashlib, json, math, re, subprocess, wave
from pathlib import Path
from prepare_audio import probe, audio_duration, validate_transcript, run, SAMPLE_RATE
from vendor.clean_talking_video.build_edit_plan import build_draft_plan
from vendor.clean_talking_video.timeline import finalize_timeline, format_srt_timestamp

SR=SAMPLE_RATE
CATEGORIES={'retain','filler','mistake','correction','retake','redundant_repeat','pause'}
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def joined(words):
    out=''
    for word in words:
        t=str(word['text'] if isinstance(word,dict) else word)
        separator=word.get('separator_before') if isinstance(word,dict) else None
        if out and separator is not None:out+=separator
        elif out and t and out[-1].isascii() and out[-1].isalnum() and t[0].isascii() and t[0].isalnum():out+=' '
        out+=t
    return out

def canonical_transcript(value,duration):
    t=copy.deepcopy(value);validate_transcript(t,duration)
    flat=[];last_end=0
    for si,s in enumerate(t['segments']):
        if not s.get('words'):raise ValueError('Full spoken editing requires word timestamps in every segment')
        s['id']=f's{si:04}'
        # ASR can split one number/acronym into several timed words (11, AGI,
        # POC). Recover separators from the segment text, never by guessing
        # whether adjacent Latin tokens form a phrase or a single word.
        cursor=0;segment_text=s['text']
        for wi,w in enumerate(s['words']):
            if not str(w.get('text','')).strip():raise ValueError('Word text is empty')
            if float(w['start'])<last_end-1e-6:raise ValueError('Word timestamps overlap or are out of order; correct ASR first')
            w.pop('separator_before',None)
            if cursor is not None:
                rest=segment_text[cursor:];gap=rest[:len(rest)-len(rest.lstrip())];token=str(w['text'])
                if rest[len(gap):].startswith(token):
                    if wi:w['separator_before']=' ' if gap else ''
                    cursor+=len(gap)+len(token)
                else:cursor=None # mismatched ASR text: retain the conservative fallback
            last_end=float(w['end']);w['id']=f'w{len(flat):05}';w['segment_id']=s['id'];flat.append(w)
    t.update(version='talking-head-transcript.v1',duration_seconds=duration)
    return t,flat

def initialize(source,transcript,project,*,example_only=False):
    source=Path(source).resolve();transcript=Path(transcript).resolve();project=Path(project).resolve()
    if project.exists() and any(project.iterdir()):raise ValueError('Use a new empty workflow project; no overwrite')
    info=probe(source);audio=next((s for s in info['streams'] if s['codec_type']=='audio'),None)
    video=next((s for s in info['streams'] if s['codec_type']=='video'),None)
    if not audio:raise ValueError('Source needs an audio stream')
    if video and abs(float(video.get('start_time',0))-float(audio.get('start_time',0)))>1/SR:
        raise ValueError('Source audio/video time origins differ; explicitly align before import')
    duration=audio_duration(source);t,words=canonical_transcript(read(transcript),duration)
    project.mkdir(parents=True,exist_ok=True);original=project/'normalized-source.wav'
    run('ffmpeg','-v','error','-xerror','-n','-i',source,'-map','0:a:0','-ar',SR,'-c:a','pcm_s24le',original)
    with wave.open(str(original),'rb') as w:total=w.getnframes()
    if abs(total/SR-duration)>.02:raise ValueError('Normalized source duration changed')
    write(project/'transcript.json',t)
    import uuid
    manifest={'schema':'draftcut.source.v2','project_id':str(uuid.uuid4()),'source':str(source),'source_sha256':sha(source),
              'original_transcript':str(transcript),'original_transcript_sha256':sha(transcript),'transcript_sha256':sha(project/'transcript.json'),
              'normalized_sha256':sha(original),'source_samples':total,'sample_rate':SR,'has_video':bool(video),'example_only':example_only}
    write(project/'source.json',manifest)
    hints=build_draft_plan(t)
    draft={'schema':'draftcut.manuscript.v2','revision':1,'source_sha256':manifest['source_sha256'],
           'decisions':[{'id':w['id'],'action':'keep','category':'retain','reason':'Preserve the source expression.'} for w in words],
           'order':[w['id'] for w in words],'pause_deletions':[],'protected_terms':[], 'corrections':{},
           'reviewed_word_ids':[],'reorder_reason':'','candidate_review_items':hints['review_items'],
           'suggested_pause_keep_segments':hints['base_keep_segments']}
    write(project/'manuscript.json',draft)
    return manifest

def source_state(project):
    p=Path(project);m=read(p/'source.json')
    if m.get('schema')!='draftcut.source.v2':raise ValueError('Legacy project: explicitly migrate and obtain both new human approvals')
    for path,expected in [(Path(m['source']),m['source_sha256']),(Path(m['original_transcript']),m['original_transcript_sha256']),
                          (p/'transcript.json',m['transcript_sha256']),(p/'normalized-source.wav',m['normalized_sha256'])]:
        if not path.is_file() or sha(path)!=expected:raise ValueError('Source/material hash changed; import a new project and review again')
    t,words=canonical_transcript(read(p/'transcript.json'),m['source_samples']/SR)
    return m,t,words

def protected(word,terms):
    t=word['text']
    return bool(re.search(r'\d|[一二三四五六七八九十百千万亿]|不|没|无|未|别|[A-Z][A-Za-z0-9]*',t)) or any(x in t for x in terms)

def compile_edit(project):
    p=Path(project);m,t,words=source_state(p);d=read(p/'manuscript.json');lookup={w['id']:w for w in words};ids=set(lookup)
    if d.get('schema')!='draftcut.manuscript.v2' or d.get('source_sha256')!=m['source_sha256']:raise ValueError('Manuscript source/schema mismatch')
    if type(d.get('revision')) is not int or d['revision']<1:raise ValueError('Manuscript revision must be a positive integer')
    rows=d.get('decisions',[])
    if len(rows)!=len(ids) or {x.get('id') for x in rows}!=ids:raise ValueError('Every source word needs exactly one keep/delete decision')
    decisions={x['id']:x for x in rows}
    if set(d.get('reviewed_word_ids',[]))!=ids:raise ValueError('Read the entire transcript; every word must be reviewed')
    for wid,row in decisions.items():
        if row.get('action') not in ('keep','delete') or row.get('category') not in CATEGORIES or not str(row.get('reason','')).strip():raise ValueError('Each decision requires an action, category and reason')
        if row['action']=='delete' and protected(lookup[wid],d.get('protected_terms',[])) and not str(row.get('sensitive_change_reason','')).strip():
            raise ValueError('Protected negation/number/name deletion needs an explicit sensitive-change reason: '+wid)
    order=d.get('order',[]);kept={i for i,x in decisions.items() if x['action']=='keep'}
    if not order or len(order)!=len(kept) or set(order)!=kept:raise ValueError('Order must contain every retained word exactly once; no invented, repeated or missing words')
    natural=[w['id'] for w in words if w['id'] in kept]
    if order!=natural and not str(d.get('reorder_reason','')).strip():raise ValueError('Reordering needs a stated reason for human review')
    corrections=d.get('corrections',{})
    if set(corrections)-kept:raise ValueError('Corrections may refer only to retained source words')
    for wid,c in corrections.items():
        if protected(lookup[wid],d.get('protected_terms',[])) and c.get('text')!=lookup[wid]['text'] and not str(c.get('sensitive_change_reason','')).strip():raise ValueError('Protected ASR correction needs an explicit sensitive-change reason: '+wid)
        evidence=c.get('evidence') or c.get('listening_evidence')
        if not all(isinstance(c.get(k),str) and c[k].strip() for k in ('text','reason')) or not isinstance(evidence,str) or not evidence.strip():
            raise ValueError('ASR correction needs text, reason and evidence (ASR, source draft, user confirmation or optional listening); never add unspoken words')
    # Group retained words into contiguous source runs, in the approved output order.
    indices={w['id']:i for i,w in enumerate(words)};runs=[]
    for wid in order:
        i=indices[wid]
        if runs and i==runs[-1][-1]+1:runs[-1].append(i)
        else:runs.append([i])
    pauses=[]
    for q in d.get('pause_deletions',[]):
        a,b=float(q['start']),float(q['end'])
        if not all(math.isfinite(v) for v in (a,b)) or a<0 or b<=a or b>m['source_samples']/SR or not str(q.get('reason','')).strip():raise ValueError('Pause deletion needs bounded timestamps and a reason')
        if any(a<float(w['end'])-1e-9 and b>float(w['start'])+1e-9 for w in words):raise ValueError('Pause deletion overlaps speech; do not swallow a word')
        pauses.append({'start':a,'end':b})
    segments=[];out=0
    for group in runs:
        first,last=group[0],group[-1]
        start=0 if first==0 else (float(words[first-1]['end'])+float(words[first]['start']))/2
        end=m['source_samples']/SR if last==len(words)-1 else (float(words[last]['end'])+float(words[last+1]['start']))/2
        v=finalize_timeline({'version':'talking-head-edit-plan.v1','source_duration_seconds':m['source_samples']/SR,
                             'base_keep_segments':[{'start':start,'end':end}], 'delete_ranges':pauses})
        for s in v['segments']:
            a=max(0,math.floor(s['start']*SR+1e-6));b=min(m['source_samples'],math.ceil(s['end']*SR-1e-6))
            if b<=a:raise ValueError('Empty sample interval')
            segments.append({'source_start_sample':a,'source_end_sample':b,'output_start_sample':out});out+=b-a
    mapped=[]
    for wid in order:
        w=lookup[wid];a=math.floor(float(w['start'])*SR+1e-6);b=math.ceil(float(w['end'])*SR-1e-6)
        matches=[s for s in segments if s['source_start_sample']<=a and s['source_end_sample']>=b]
        if len(matches)!=1:raise ValueError('A retained word was split, duplicated or removed: '+wid)
        s=matches[0];oa=s['output_start_sample']+a-s['source_start_sample'];ob=s['output_start_sample']+b-s['source_start_sample']
        mapped.append({'id':wid,'text':corrections.get(wid,{}).get('text',w['text']),'source_text':w['text'],
                       'separator_before':w.get('separator_before'),
                       'source_start_sample':a,'source_end_sample':b,'start_sample':oa,'end_sample':ob,'start':oa/SR,'end':ob/SR})
    # No kept interval may include even part of a deliberately deleted word.
    for wid,row in decisions.items():
        if row['action']=='delete':
            w=lookup[wid];a=math.floor(float(w['start'])*SR+1e-6);b=math.ceil(float(w['end'])*SR-1e-6)
            if any(s['source_start_sample']<b and s['source_end_sample']>a for s in segments):raise ValueError('Deletion still contains spoken samples: '+wid)
    groups=d.get('caption_groups') or [[wid] for wid in order]
    if [i for g in groups for i in g]!=order:raise ValueError('Caption groups must cover retained words once in output order')
    by_id={w['id']:w for w in mapped};captions=[]
    for group in groups:
        ws=[by_id[i] for i in group]
        if not ws:raise ValueError('Empty caption group')
        captions.append({'start':ws[0]['start'],'end':ws[-1]['end'],'text':joined(ws),'word_ids':group})
    blocks=[]
    for i,c in enumerate(captions,1):
        if round(c['end']*1000)<=round(c['start']*1000):raise ValueError('Caption is shorter than SRT millisecond precision; group adjacent words')
        blocks.append(f"{i}\n{format_srt_timestamp(c['start'])} --> {format_srt_timestamp(c['end'])}\n{c['text']}")
    return {'schema':'draftcut.edit-timeline.v2','sample_rate':SR,'source_samples':m['source_samples'],'output_samples':out,
            'duration_seconds':out/SR,'segments':segments,'words':mapped,'captions':captions,'srt':'\n\n'.join(blocks)+'\n',
            'source_text':joined(words),'refined_text':joined(mapped),'reordered':order!=natural}

def splice(project,timeline,destination):
    destination=Path(destination)
    if destination.exists():raise ValueError('Preserve prior output; audio destination already exists')
    expected=hashlib.sha256();destination.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(Path(project)/'normalized-source.wav'),'rb') as src,wave.open(str(destination),'wb') as dst:
        dst.setparams(src.getparams());width=src.getsampwidth()*src.getnchannels()
        for s in timeline['segments']:
            src.setpos(s['source_start_sample']);remaining=s['source_end_sample']-s['source_start_sample']
            while remaining:
                count=min(remaining,16384);b=src.readframes(count)
                if len(b)!=count*width:raise ValueError('Source PCM truncated at splice')
                dst.writeframesraw(b);expected.update(b);remaining-=count
    with wave.open(str(destination),'rb') as actual:
        if actual.getnframes()!=timeline['output_samples']:raise ValueError('Output sample count mismatch')
        actual_hash=hashlib.sha256(actual.readframes(actual.getnframes())).hexdigest()
    if actual_hash!=expected.hexdigest():raise ValueError('Output PCM differs from retained source samples')
    run('ffmpeg','-v','error','-xerror','-i',destination,'-f','null','-')
    return {'audio_sha256':sha(destination),'pcm_sha256':actual_hash,'samples':timeline['output_samples'],'sample_rate':SR}

def render_presenter(project,timeline,audio,destination,fps=30):
    m,_,_=source_state(project)
    if not m['has_video']:return None
    n=len(timeline['segments']);parts=[f'[0:v]fps={fps},split={n}'+''.join(f'[src{i}]' for i in range(n))];previous=0
    for i,s in enumerate(timeline['segments']):
        end=round((s['output_start_sample']+s['source_end_sample']-s['source_start_sample'])/SR*fps);count=end-previous
        if count<1:raise ValueError('A video splice is shorter than one frame; revise the edit')
        a=s['source_start_sample']/SR;b=s['source_end_sample']/SR
        parts.append(f'[src{i}]trim=start={a:.9f}:end={b:.9f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1,trim=end_frame={count},setpts=N/({fps}*TB)[v{i}]');previous=end
    parts.append(''.join(f'[v{i}]' for i in range(n))+f'concat=n={n}:v=1:a=0,trim=duration={timeline["duration_seconds"]:.9f}[out]')
    script=Path(destination).with_suffix('.ffgraph');script.write_text(';\n'.join(parts))
    run('ffmpeg','-v','error','-xerror','-n','-i',m['source'],'-i',audio,'-filter_complex_script',script,'-map','[out]','-map','1:a:0',
        '-c:v','libx264','-preset','fast','-crf','18','-c:a','aac','-t',timeline['duration_seconds'],'-movflags','+faststart',destination)
    run('ffmpeg','-v','error','-xerror','-i',destination,'-f','null','-')
    info=probe(destination)
    for stream in info['streams']:
        if stream['codec_type'] in ('audio','video') and abs(float(stream.get('duration',info['format']['duration']))-timeline['duration_seconds'])>2/fps:
            raise ValueError('Edited presenter A/V duration mismatch')
    return {'path':str(Path(destination).resolve()),'sha256':sha(destination),'fps':fps,'frame_rounding_bound_seconds':1/fps}

def verify_splice(project,timeline,audio):
    """Recompute source PCM rather than trusting an editable preparation report."""
    with wave.open(str(Path(project)/'normalized-source.wav'),'rb') as src,wave.open(str(audio),'rb') as dst:
        if (src.getnchannels(),src.getsampwidth(),src.getframerate())!=(dst.getnchannels(),dst.getsampwidth(),dst.getframerate()):raise ValueError('Approved master PCM format changed')
        if dst.getnframes()!=timeline['output_samples']:raise ValueError('Approved master sample count changed')
        for s in timeline['segments']:
            src.setpos(s['source_start_sample']);remaining=s['source_end_sample']-s['source_start_sample']
            while remaining:
                n=min(16384,remaining)
                if src.readframes(n)!=dst.readframes(n):raise ValueError('Prepared audio is not the approved original-voice splice')
                remaining-=n
        if dst.readframes(1):raise ValueError('Prepared audio has extra samples')
