#!/usr/bin/env python3
"""Render a clean talking-head cut after the Agent receives explicit manuscript approval.

The approval note is an audit note, not a cryptographic receipt. Authorization is
checked by the hosting Agent against the actual user conversation before invocation.
"""
from __future__ import annotations
import argparse,json,re,subprocess
from fractions import Fraction
from pathlib import Path
from spoken_edit import source_state,compile_edit,splice,verify_splice,read,write,sha,SR
from prepare_audio import probe

def frame_allocations(timeline,fps):
    previous=0;rows=[]
    for s in timeline['segments']:
        stop=round((s['output_start_sample']+s['source_end_sample']-s['source_start_sample'])/SR*fps)
        count=stop-previous
        if count<1:raise ValueError('A source cut is shorter than one output frame')
        rows.append({**s,'output_start_frame':previous,'output_end_frame':stop,'frame_count':count})
        previous=stop
    return rows

def validate_subtitles(path,duration):
    text=Path(path).read_text();previous=0.;count=0
    for block in re.split(r'\n\s*\n',text.strip()):
        lines=block.splitlines()
        if len(lines)<3 or not lines[0].strip().isdigit():raise ValueError('Malformed SRT caption')
        match=re.fullmatch(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})',lines[1].strip())
        if not match:raise ValueError('Malformed SRT timing')
        values=list(map(int,match.groups()))
        def seconds(v):return v[0]*3600+v[1]*60+v[2]+v[3]/1000
        a,b=seconds(values[:4]),seconds(values[4:])
        if not 0<=a<b<=duration+.001 or a<previous-.001:raise ValueError('SRT boundaries are outside or overlap the clean timeline')
        if not ''.join(lines[2:]).strip():raise ValueError('SRT caption has no text')
        previous=b;count+=1
    if not count:raise ValueError('SRT captions are empty')
    return count

def command(args,log):
    with log.open('a') as out:
        subprocess.run([str(x) for x in args],check=True,stdout=out,stderr=out)

def render(project,output,encoding,approval_note,subtitles=None):
    project=Path(project).resolve();output=Path(output).resolve()
    if not approval_note.strip():raise ValueError('Record the actual user approval and scope before invoking clean render')
    if output.exists() and any(output.iterdir()):raise ValueError('Use a new empty output directory; preserve prior renders')
    m,_,_=source_state(project)
    if m.get('example_only') or m.get('simulation_run'):raise ValueError('This clean-production command does not promote fixtures or simulations')
    if not m['has_video']:raise ValueError('Clean video delivery requires presenter footage')
    t=compile_edit(project)
    from spoken_workflow import semantic_evidence
    semantic_evidence(project,t)
    info=probe(Path(m['source']));video=next(x for x in info['streams'] if x['codec_type']=='video')
    fps=float(Fraction(video['r_frame_rate']));frames=frame_allocations(t,fps)
    if subtitles:
        subtitles=Path(subtitles).resolve()
        if not subtitles.is_file():raise ValueError('Subtitle input is missing')
        validate_subtitles(subtitles,t['duration_seconds'])
    output.mkdir(parents=True,exist_ok=True);parts=output/'parts';parts.mkdir();log=output/'render.log'
    # Seal the exact proposed word decisions and render intent before encoding.
    write(output/'render-inputs.json',{'source':m,'manuscript_sha256':sha(project/'manuscript.json'),
          'approval_note':approval_note,'approval_channel':'direct-user-conversation-checked-by-host-agent',
          'cryptographic_receipt':False,'encoding':encoding,'subtitles_sha256':sha(subtitles) if subtitles else None,
          'frame_allocations':frames,'fps':fps,'width':video['width'],'height':video['height']})
    audio=output/'narration.wav';splice(project,t,audio);verify_splice(project,t,audio)
    outputs=[]
    for i,s in enumerate(frames):
        dest=parts/f'{i:03}.mp4';a=s['source_start_sample']/SR;b=s['source_end_sample']/SR
        codec=['-c:v','h264_videotoolbox','-b:v','24M','-allow_sw','0'] if encoding=='hardware' else ['-c:v','libx264','-preset','fast','-crf','18']
        filters=f'fps={fps:.9f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={1/fps:.9f},trim=end_frame={s["frame_count"]},setpts=N/({fps:.9f}*TB)'
        command(['ffmpeg','-nostdin','-v','error','-xerror','-n','-ss',f'{a:.9f}','-i',m['source'],'-t',f'{b-a+2/fps:.9f}',
                 '-map','0:v:0','-an','-vf',filters,'-frames:v',s['frame_count'],*codec,'-pix_fmt','yuv420p',
                 *[item for field,flag in [('color_primaries','-color_primaries'),('color_transfer','-color_trc'),('color_space','-colorspace')]
                   if video.get(field) not in (None,'unknown','unspecified') for item in (flag,video[field])],
                 '-video_track_timescale','60000',dest],log)
        got=probe(dest);vs=next(x for x in got['streams'] if x['codec_type']=='video')
        if int(vs.get('nb_frames',-1))!=s['frame_count']:raise ValueError('Encoded source cut frame count mismatch')
        outputs.append(dest);print(f'Clean cut {i+1}/{len(frames)} encoded',flush=True)
    listing=output/'concat.txt';listing.write_text(''.join("file 'parts/"+f.name+"'\nduration "+f'{row["frame_count"]/fps:.9f}'+"\n" for f,row in zip(outputs,frames)))
    combined=output/'picture.mp4';command(['ffmpeg','-nostdin','-v','error','-xerror','-n','-f','concat','-safe','0','-i',listing,'-c','copy',combined],log)
    final=output/'edited-video.mp4';command(['ffmpeg','-nostdin','-v','error','-xerror','-n','-i',combined,'-i',audio,
          '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-t',f'{t["duration_seconds"]:.9f}',
          '-movflags','+faststart',final],log)
    command(['ffmpeg','-nostdin','-v','error','-xerror','-i',final,'-f','null','-'],log)
    final_info=probe(final);vs=next(x for x in final_info['streams'] if x['codec_type']=='video');au=next(x for x in final_info['streams'] if x['codec_type']=='audio')
    if int(vs['nb_frames'])!=frames[-1]['output_end_frame']:raise ValueError('Final video frame count mismatch')
    for stream in (vs,au):
        if abs(float(stream['duration'])-t['duration_seconds'])>2/fps:raise ValueError('Final stream duration mismatch')
    from verify_output_audio import compare_audio
    waveform=compare_audio(audio,final)
    import shutil
    if subtitles:shutil.copyfile(subtitles,output/'final-clean.srt')
    else:(output/'final-clean.srt').write_text(t['srt'])
    caption_count=validate_subtitles(output/'final-clean.srt',t['duration_seconds'])
    # A render must not race a manuscript edit or replace the audited source.
    source_state(project)
    if sha(project/'manuscript.json')!=read(output/'render-inputs.json')['manuscript_sha256']:raise ValueError('Manuscript changed during render')
    report={'stage':'clean-cut','status':'technical-passed','video':str(final),'video_sha256':sha(final),'duration_seconds':t['duration_seconds'],
            'width':vs['width'],'height':vs['height'],'fps':fps,'frames':int(vs['nb_frames']),'audio_codec':au['codec_name'],
            'full_decode':'passed','source_pcm_match':'passed','waveform':waveform,'visual_review':'pending','hearing':'not-tested',
            'packaging':False,'burned_subtitles':False,'subtitle_captions':caption_count,'cryptographic_receipt':False,'subtitle_sha256':sha(output/'final-clean.srt')}
    write(output/'quality-report.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--encoding',choices=['hardware','software'],default='hardware');p.add_argument('--approval-note',required=True);p.add_argument('--subtitles',type=Path)
    a=p.parse_args();render(a.project_dir,a.output_dir,a.encoding,a.approval_note,a.subtitles)
if __name__=='__main__':main()
