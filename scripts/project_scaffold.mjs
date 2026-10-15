export const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function visualFrameEnd(duration, fps) {
  if (!(Number.isFinite(duration) && duration > 0 && Number.isFinite(fps) && fps > 0))
    throw new Error('Visual duration and fps must be positive finite numbers');
  // Cover every captured frame, without a floating-point overshoot creating another frame.
  return Math.floor(Math.max(1, Math.ceil(duration * fps - 1e-9)) / fps * 1e9) / 1e9;
}
export function parseSrt(text) {
  const seconds = t => {const [h,m,s] = t.replace(',', '.').split(':').map(Number); return h*3600+m*60+s;};
  let previous = -1;
  if (!text.trim()) throw new Error('SRT must contain captions');
  return text.replace(/^\uFEFF/, '').trim().split(/\r?\n\s*\r?\n/).filter(Boolean).map(block => {
    const rows = block.split(/\r?\n/);
    const timing = rows.findIndex(row => row.includes('-->'));
    const match = rows[timing]?.match(/(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})/);
    if (!match) throw new Error('Invalid SRT timestamp');
    const start = seconds(match[1]), end = seconds(match[2]);
    if (end <= start || start < previous) throw new Error('Invalid or out-of-order SRT cue');
    previous = start;
    if (!rows.slice(timing+1).join('').trim()) throw new Error('SRT cue needs text');
    return {start, end, text: rows.slice(timing+1).join('\n')};
  });
}
export function scaffold(plan, captions) {
  const {width:w, height:h, fps} = plan.render_spec, duration = plan.source.duration_seconds;
  const visualEnd = visualFrameEnd(duration, fps);
  const cueEnd = (cue, index) => index === plan.cues.length - 1 && Math.abs(cue.end_seconds-duration) <= 1/fps + 1e-6 ? visualEnd : cue.end_seconds;
  const captionHtml = captions.map((c,i) => {
    if (c.start < 0 || c.end > duration+.001) throw new Error('Subtitle exceeds approved audio timeline');
    return `<div id="caption-${i}" class="clip caption caption-${i}" data-start="${c.start}" data-duration="${c.end-c.start}" data-track-index="10">${escapeHtml(c.text)}</div>`;
  }).join('\n');
  const cueHtml = plan.cues.map((c,i)=>`<section id="scene-${i}" class="clip scene scene-${i}" data-start="${c.start_seconds}" data-duration="${cueEnd(c,i)-c.start_seconds}" data-track-index="1"><div id="headline-${i}" class="headline headline-${i}">${escapeHtml(c.title || c.visual_prompt)}</div></section>`).join('\n');
  const motion = [
    `gsap.set('.scene, .caption',{autoAlpha:0});`,
    ...plan.cues.map((c,i)=>`timeline.set('.scene-${i}',{autoAlpha:1},${c.start_seconds});timeline.fromTo('.headline-${i}',{y:24,autoAlpha:0},{y:0,autoAlpha:1,duration:0.25},${c.start_seconds});timeline.set('.scene-${i}',{autoAlpha:0},${cueEnd(c,i)});`),
    ...captions.map((c,i)=>`timeline.set('.caption-${i}',{autoAlpha:1},${c.start});timeline.set('.caption-${i}',{autoAlpha:0},${c.end});`),
  ].join('\n');
  return `<!doctype html>
<html lang="${escapeHtml(plan.language || 'zh-CN')}"><head><meta charset="utf-8"><title>DraftCut</title>
<script src="assets/gsap.min.js"></script><link rel="stylesheet" href="theme.css"></head>
<body><div id="master" data-composition-id="master" data-start="0" data-duration="${visualEnd}" data-width="${w}" data-height="${h}" data-fps="${fps}">
<div id="background" class="background"></div>
${plan.simulation_run?'<div id="draftcut-test-watermark" style="position:absolute;z-index:9999;top:12px;right:12px;padding:8px 12px;background:#111c;color:#fff;font:14px sans-serif;pointer-events:none">SIMULATED USER TEST · HEARING NOT TESTED</div>':''}
${cueHtml}
<audio id="main-audio" class="clip" data-start="0" data-duration="${duration}" data-track-index="20" src="assets/narration.wav" data-volume="1"></audio>
${captionHtml}
</div><script>const timeline=gsap.timeline({paused:true});${motion}
window.__timelines=window.__timelines||{};window.__timelines.master=timeline;</script></body></html>\n`;
}
