#!/usr/bin/env python3
"""Loopback seek-safe composition preview when the pinned Studio viewer misbehaves."""
import argparse,functools,http.server
from pathlib import Path

PAGE='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>DraftCut 本地连续预览</title>
<style>body{margin:0;background:#17202b;color:#f1f5f9;font:16px system-ui}main{padding:24px;max-width:1100px;margin:auto}h1{font-size:20px}iframe{border:0;background:#111;display:block}button,input{font:inherit}button{padding:9px 20px}nav{display:flex;gap:15px;align-items:center;padding:18px 0}input{flex:1}p{color:#aebdd0}</style>
<main><h1>DraftCut 本地连续预览</h1><p>同一工程、同一原声、同一暂停时间线。此页面不批准稿件或视频脚本。</p>
<iframe id="frame" src="/index.html" title="视频画面"></iframe><nav><button id="play" disabled>播放</button><input id="seek" aria-label="播放进度" type="range" min="0" max="1" step="0.001" value="0"><output id="clock">加载中</output></nav><p id="status">等待工程</p></main>
<script>
const frame=document.getElementById('frame'),button=document.getElementById('play'),slider=document.getElementById('seek'),clock=document.getElementById('clock'),status=document.getElementById('status');
let duration=0,playing=false,win,timeline,audio,clips=[],origin=0,time=0;
function seek(t){time=Math.max(0,Math.min(duration,t));timeline.pause().time(time,false);
 for(const node of clips){const a=Number(node.dataset.start||0),b=a+Number(node.dataset.duration||duration);node.style.display=(time>=a&&time<b)?'':'none';
  if(node.tagName==='VIDEO'){node.muted=true;const mediaStart=Number(node.dataset.mediaStart||0);const wanted=Math.max(0,time-a+mediaStart);if(Math.abs(node.currentTime-wanted)>.05)node.currentTime=wanted;}}
 slider.value=time;clock.value=time.toFixed(3)+' / '+duration.toFixed(3)+' 秒';}
function stop(){playing=false;audio?.pause();button.textContent='播放';}
function tick(){if(!playing)return;const t=audio?audio.currentTime:(performance.now()-origin)/1000;seek(t);if(t>=duration-.002||audio?.ended){seek(duration);stop();status.textContent='完整播放结束';return;}requestAnimationFrame(tick);}
button.onclick=async()=>{if(playing){stop();status.textContent='已暂停';return;}if(time>=duration-.002)seek(0);if(audio){audio.currentTime=time;try{await audio.play();}catch(e){status.textContent='音频播放失败：'+e.message;return;}}playing=true;origin=performance.now()-time*1000;button.textContent='暂停';status.textContent='连续播放中';requestAnimationFrame(tick);};
slider.oninput=()=>{stop();seek(Number(slider.value));if(audio)audio.currentTime=time;status.textContent='已定位';};
frame.onload=()=>{win=frame.contentWindow;const root=win.document.querySelector('[data-composition-id]');timeline=win.__timelines?.master;if(!root||!timeline){status.textContent='缺少 master 暂停时间线';return;}duration=Number(root.dataset.duration);frame.width=Number(root.dataset.width);frame.height=Number(root.dataset.height);audio=win.document.getElementById('main-audio');clips=[...win.document.querySelectorAll('.clip[data-start]')];slider.max=duration;button.disabled=false;seek(0);status.textContent='可播放 · 仅本机回环服务';};
</script></html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?')[0]=='/__draftcut_preview__':
            b=PAGE.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        resolved=Path(self.translate_path(self.path)).resolve()
        if not resolved.is_relative_to(Path(self.directory).resolve()):self.send_error(403);return
        super().do_GET()
    def log_message(self,*args):pass

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project-dir',type=Path,required=True);p.add_argument('--port',type=int,default=3042);args=p.parse_args();root=args.project_dir.resolve()
    if not (root/'index.html').is_file():p.error('Project index.html is missing')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',args.port),functools.partial(Handler,directory=str(root)))
    print(f'Local preview: http://127.0.0.1:{args.port}/__draftcut_preview__',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
