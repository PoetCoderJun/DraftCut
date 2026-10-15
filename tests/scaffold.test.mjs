import test from 'node:test';
import assert from 'node:assert/strict';
import {parseSrt,scaffold,visualFrameEnd} from '../scripts/project_scaffold.mjs';
import {checkMetadata} from '../scripts/validate_master.mjs';
import {buildRenderArgs} from '../scripts/render_master.mjs';
import {readFileSync} from 'node:fs';
const plan=JSON.parse(readFileSync(new URL('../examples/plan-validation/plan.json',import.meta.url)));
test('SRT validates malformed timestamps and escapes user text',()=>{assert.throws(()=>parseSrt(''));assert.throws(()=>parseSrt('1\n00:00:01,000 --> 00:00:00,000\nx'));const html=scaffold(plan,parseSrt('1\n00:00:00,000 --> 00:00:01,000\n<script>alert(1)</script>'));assert.match(html,/&lt;script&gt;/);assert.equal((html.match(/<audio /g)||[]).length,1);assert.doesNotMatch(html,/<video/);});
test('caption outside audio timeline is rejected',()=>assert.throws(()=>scaffold(plan,[{start:0,end:3,text:'x'}])));
test('technical check detects truncated audio independently of video',()=>{const m={streams:[{codec_type:'video',codec_name:'h264',width:640,height:360,avg_frame_rate:'30/1',duration:'2'},{codec_type:'audio',codec_name:'aac',duration:'2'}]};assert.ok(Object.values(checkMetadata(plan,m)).every(Boolean));m.streams[1].duration='1';assert.equal(checkMetadata(plan,m).audio_timeline,false);});
test('software render is explicit and keeps deterministic strict settings',()=>{const args=buildRenderArgs({projectDir:'p',output:'o',fps:30,encoding:'software'});assert.ok(args.includes('--no-browser-gpu'));assert.ok(!args.includes('--gpu'));assert.ok(args.includes('--strict'));});
test('visual frame end covers the last captured frame without creating an extra frame',()=>{
  for(const duration of [216.50133333333332,2,61/30,2.000020833333333,1/48000]){
    const frames=Math.ceil(duration*30),end=visualFrameEnd(duration,30);
    assert.ok(end>(frames-1)/30);
    assert.equal(Math.ceil(end*30),frames);
  }
});
test('last scene and root cover fractional audio tail while approved audio timing stays exact',()=>{
  const duration=216.50133333333332;
  const p={...plan,source:{...plan.source,duration_seconds:duration},simulation_run:{run_id:'test'},cues:[{start_seconds:206.06666666666666,end_seconds:216.5,title:'Ending'}]};
  const html=scaffold(p,[{start:0,end:1,text:'x'}]);
  assert.match(html,/data-composition-id="master" data-start="0" data-duration="216\.533333333"/);
  assert.match(html,/id="main-audio"[^>]*data-duration="216\.50133333333332"/);
  assert.match(html,/timeline\.set\('\.scene-0',\{autoAlpha:0\},216\.533333333\)/);
  assert.match(html,/draftcut-test-watermark/);
});
