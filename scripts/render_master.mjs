#!/usr/bin/env node
import {readFile, mkdir, mkdtemp, copyFile, writeFile} from 'node:fs/promises';
import {createWriteStream, existsSync, constants} from 'node:fs';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseArgs, runCli, mediaMetadata} from './hyperframes_runtime.mjs';
import {resolveBrowserExecutable} from './local_browser.mjs';
import {acquireRenderLock} from './render_lock.mjs';

export function buildRenderArgs({projectDir, output, fps, videoBitrate, encoding = 'hardware'}) {
  return ['render', projectDir, '--output', output, '--fps', String(fps),
    '--format', 'mp4', '--quality', 'high', '--workers', '1', '--max-concurrent-renders', '1',
    ...(encoding === 'hardware' ? ['--gpu','--browser-gpu'] : ['--no-browser-gpu']),
    '--sdr', '--strict', '--no-best-effort',
    ...(videoBitrate ? ['--video-bitrate', videoBitrate] : [])];
}
async function main() {
  const args = parseArgs(process.argv.slice(2), ['project_dir','plan','output','video_bitrate','browser_executable','workers','encoding','purpose']);
  if (args.help) return console.log('Usage: node render_master.mjs --project-dir DIR/hyperframes --plan PLAN.json --output FINAL.mp4 [--video-bitrate 12M] [--browser-executable CHROME]\nDefault: one worker, native Chrome, hardware H.264. --encoding software is explicit. --purpose smoke permits unfinished synthetic scaffolds; production requires recorded visual review.');
  if (!args.project_dir || !args.plan || !args.output) throw new Error('--project-dir, --plan and --output are required');
  if (args.workers !== undefined && args.workers !== '1') throw new Error('DraftCut requires --workers 1');
  const encoding = args.encoding || 'hardware', purpose = args.purpose || 'production';
  if (!['hardware','software'].includes(encoding) || !['production','smoke'].includes(purpose)) throw new Error('Invalid encoding or purpose');
  const projectDir = path.resolve(args.project_dir), output = path.resolve(args.output);
  if (purpose === 'production') {
    const state = JSON.parse(await readFile(path.join(projectDir,'project-state.json'),'utf8'));
    if (state.status !== 'ready' || state.needs_visual_production !== false || state.visual_review?.scope !== 'continuous' || !state.visual_review?.evidence?.length)
      throw new Error('Complete the approved visual production and record continuous preview evidence before production export');
    for (const evidence of state.visual_review.evidence) {
      if (typeof evidence !== 'string' || !existsSync(path.resolve(projectDir,evidence)))
        throw new Error('Recorded visual review evidence does not exist');
    }
  }
  if (existsSync(output)) throw new Error('Preserve the previous export; choose a new output path');
  const plan = JSON.parse(await readFile(path.resolve(args.plan),'utf8'));
  if (purpose === 'smoke' && plan.example_only !== true) throw new Error('Smoke rendering requires an explicitly marked synthetic example plan');
  if (plan.status !== 'approved' || plan.approved !== true) throw new Error('Director plan must be approved');
  const fps = plan.render_spec?.fps;
  if (!Number.isFinite(fps) || fps <= 0) throw new Error('Invalid render fps');
  const release = await acquireRenderLock(projectDir);
  const started = performance.now();
  const logPath = path.join(projectDir, 'render.log');
  let log;
  try {
    const browser = resolveBrowserExecutable(args.browser_executable);
    const ffmpeg = process.env.HYPERFRAMES_FFMPEG_PATH || 'ffmpeg';
    if (encoding === 'hardware' && process.platform === 'darwin') {
      execFileSync(ffmpeg, ['-hide_banner','-loglevel','error','-f','lavfi','-i',
        'color=size=320x240:rate=1:duration=1','-frames:v','1','-c:v','h264_videotoolbox','-allow_sw','0','-f','null','-'],
        {stdio:'pipe',timeout:15000});
    }
    await mkdir(path.dirname(output),{recursive:true});
    log = createWriteStream(logPath);
    // Keep renderer transactions/intermediates outside the single-file delivery directory.
    await mkdir(path.join(projectDir,'.renders'),{recursive:true});
    const stagingDir = await mkdtemp(path.join(projectDir,'.renders','export-'));
    const stagedOutput = path.join(stagingDir,'render.mp4');
    const command = buildRenderArgs({projectDir,output:stagedOutput,fps,videoBitrate:args.video_bitrate,encoding});
    console.log('Hyperframes '+purpose+' export started: one worker, '+encoding+' encoding. Log: '+logPath);
    await runCli(command,{cwd:projectDir,capture:true,log,env:{
      HYPERFRAMES_BROWSER_PATH:browser, PRODUCER_HEADLESS_SHELL_PATH:browser,
      PRODUCER_BROWSER_GPU_MODE:encoding === 'hardware' ? 'hardware' : 'software', PRODUCER_DISABLE_GPU:encoding === 'hardware' ? 'false' : 'true',
    }});
    const media = mediaMetadata(stagedOutput);
    const video=media.streams.find(s=>s.codec_type==='video'), audio=media.streams.find(s=>s.codec_type==='audio');
    if (video?.codec_name!=='h264' || audio?.codec_name!=='aac') throw new Error('Export must contain H.264 video and AAC audio');
    await copyFile(stagedOutput,output,constants.COPYFILE_EXCL);
    const metrics={status:'completed',engine:'hyperframes',workers:1,node:process.execPath,
      architecture:process.arch,browserExecutable:browser,purpose,hardwareEncodingRequested:encoding==='hardware',
      totalSeconds:(performance.now()-started)/1000,output,stagedOutput,logPath,command};
    await writeFile(path.join(projectDir,'render-metrics.v1.json'),JSON.stringify(metrics,null,2)+'\n');
    console.log('Completed: '+output);
  } finally {log?.end(); await release();}
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(e=>{console.error(e.message);process.exitCode=1;});
}
