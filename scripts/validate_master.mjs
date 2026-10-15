#!/usr/bin/env node
import {readFile, readdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs, mediaMetadata} from './hyperframes_runtime.mjs';

export function checkMetadata(plan, metadata) {
  const video = metadata.streams?.find(s=>s.codec_type==='video');
  const audio = metadata.streams?.find(s=>s.codec_type==='audio');
  const spec=plan.render_spec || {};
  const [n,d]=String(video?.avg_frame_rate || video?.r_frame_rate || '0/1').split('/').map(Number);
  const fps=n/(d || 1), duration=Number(video?.duration || metadata.format?.duration);
  const expected=Number(plan.source?.duration_seconds);
  return {
    approved_plan: plan.status==='approved' && plan.approved===true,
    project_render_spec: Number.isFinite(expected) && expected>0 && Number(spec.fps)>0 &&
      video?.width===Number(spec.width) && video?.height===Number(spec.height) &&
      Math.abs(fps-Number(spec.fps))<0.01 && Math.abs(duration-expected)<=3/Number(spec.fps),
    audio_timeline: Number.isFinite(Number(audio?.duration)) && Math.abs(Number(audio.duration)-expected)<=3/Number(spec.fps),
    audio_video_codecs: video?.codec_name==='h264' && audio?.codec_name==='aac',
  };
}
async function main() {
  const args=parseArgs(process.argv.slice(2),['plan','final','output_dir']);
  if(args.help)return console.log('Usage: node validate_master.mjs --plan PLAN.json --final FINAL.mp4 --output-dir OUTPUT\nTechnical metadata only; no visual evidence or Remotion dependency.');
  if(!args.plan||!args.final||!args.output_dir)throw new Error('--plan, --final and --output-dir are required');
  const final=path.resolve(args.final), output=path.resolve(args.output_dir);
  const plan=JSON.parse(await readFile(path.resolve(args.plan),'utf8'));
  const metadata=mediaMetadata(final);
  const checks=checkMetadata(plan,metadata);
  const entries=await readdir(path.dirname(final));
  checks.delivery_cleanliness=entries.length===1 && entries[0]===path.basename(final) && path.extname(final).toLowerCase()==='.mp4';
  const passed=Object.values(checks).every(Boolean);
  const report={schema_version:'motiontalk.quality-report.v1',status:passed?'passed':'failed',
    scope:'technical',engine:'hyperframes',visual_review:'not_assessed_by_this_validator',
    packaged_video:path.relative(output,final),
    checks:Object.fromEntries(Object.entries(checks).map(([k,v])=>[k,v?'passed':'failed'])),
    evidence:{media:metadata}};
  await writeFile(path.join(output,'quality-report.v1.json'),JSON.stringify(report,null,2)+'\n');
  if(!passed)throw new Error('Technical check failed: '+Object.entries(checks).filter(([,v])=>!v).map(([k])=>k).join(', '));
  console.log('DraftCut technical checks: passed');
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url))
  main().catch(e=>{console.error(e.message);process.exitCode=1;});
