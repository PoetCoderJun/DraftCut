#!/usr/bin/env node
import {readFile, mkdir, copyFile, writeFile, readdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {parseArgs, require, mediaMetadata} from './hyperframes_runtime.mjs';
import {parseSrt, scaffold} from './project_scaffold.mjs';
import {assertWorkflow} from './workflow_guard.mjs';

try {
  const args = parseArgs(process.argv.slice(2), ['project_dir', 'plan']);
  if (args.help) console.log('Usage: node init_project.mjs --project-dir OUTPUT/hyperframes --plan PLAN.json\nAudio-first scaffold; optional materials are used only as approved visual sources.');
  else {
    if (!args.plan || !args.project_dir) throw new Error('--plan and --project-dir are required');
    const planPath = path.resolve(args.plan), dir = path.resolve(args.project_dir);
    execFileSync('python3',[path.join(path.dirname(fileURLToPath(import.meta.url)),'validate_plan.py'),'--plan',planPath],{stdio:'pipe'});
    const plan = JSON.parse(await readFile(planPath,'utf8'));
    const approval=assertWorkflow(planPath);
    if(approval.simulation_run)plan.simulation_run=approval.simulation_run;
    const resolveSource = v => path.resolve(path.dirname(planPath),v);
    const audioPath = resolveSource(plan.source.audio);
    const media=mediaMetadata(audioPath), audio=media.streams?.find(s=>s.codec_type==='audio');
    if (!audio) throw new Error('Prepared source must contain audio; a video track is not required');
    const duration=Number(audio.duration || media.format?.duration);
    if(Math.abs(duration-plan.source.duration_seconds)>0.02)throw new Error('Audio duration differs from approved plan');
    const entries=await readdir(dir).catch(e=>{if(e.code==='ENOENT')return [];throw e;});
    if(entries.length)throw new Error('Preserve the existing project; initialization requires an empty directory');
    const captions=parseSrt(await readFile(resolveSource(plan.source.subtitles),'utf8'));
    const html=scaffold(plan,captions);
    await mkdir(path.join(dir,'assets'),{recursive:true});
    // Copy the signed master without changing its approved samples.
    await copyFile(audioPath,path.join(dir,'assets/narration.wav')); // Preserve the approved PCM byte-for-byte.
    await copyFile(require.resolve('gsap/dist/gsap.min.js'),path.join(dir,'assets/gsap.min.js'));
    await writeFile(path.join(dir,'final.srt'),await readFile(resolveSource(plan.source.subtitles),'utf8'));
    const {width:w,height:h}=plan.render_spec;
    await writeFile(path.join(dir,'theme.css'),`:root{--ink:#f8fafc;--accent:#7dd3fc;--font:system-ui,"PingFang SC","Noto Sans CJK SC",sans-serif;}*{box-sizing:border-box}body{margin:0;background:#101827;color:var(--ink);font-family:var(--font)}#master{position:relative;width:${w}px;height:${h}px;overflow:hidden}.background{position:absolute;inset:0;background:#101827}.scene,.caption{opacity:0;visibility:hidden}.scene{position:absolute;inset:0;display:flex;align-items:center;padding:9%;z-index:1}.headline{display:block;max-width:100%;font-size:${w*.055}px;line-height:1.25;overflow-wrap:anywhere}.caption{position:absolute;left:7%;right:7%;bottom:7%;z-index:10;text-align:center;white-space:pre-wrap;line-height:1.35;font-size:${w*.036}px;overflow-wrap:anywhere}`);
    await writeFile(path.join(dir,'index.html'),html);
    await writeFile(path.join(dir,'project-state.json'),JSON.stringify({status:'scaffold',input:'audio',needs_visual_production:true,workflow:plan.workflow,...(approval.simulation_run?{simulation_run:approval.simulation_run,owner_approval:false}: {})},null,2)+'\n');
    await writeFile(path.join(dir,'hyperframes.json'),JSON.stringify({registry:'https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry',paths:{blocks:'compositions',components:'compositions/components',assets:'assets'}},null,2)+'\n');
    console.log('Audio-first scaffold created. No presenter video assumed. Build the approved visual story and inspect it before declaring production complete.');
  }
}catch(e){console.error(e.stderr?.toString() || e.stdout?.toString() || e.message);process.exitCode=1;}
