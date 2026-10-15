"""Validate DOM captions and the single original-voice audio source before export."""
from html.parser import HTMLParser
from pathlib import Path
import math

class CompositionDOM(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.media=[];self.captions={};self.stack=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ('audio','video'):self.media.append((tag,a))
        inherited=self.stack[-1][1] if self.stack else None
        cid=a.get('id') if a.get('id','').startswith('caption-') else inherited
        if cid and cid not in self.captions:self.captions[cid]={'attrs':a,'text':''}
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append((tag,cid))
        elif tag=='br' and cid:self.captions[cid]['text']+='\n'
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):
        if self.stack and self.stack[-1][1]:self.captions[self.stack[-1][1]]['text']+=data

def check_composition(project_dir,timeline):
    p=Path(project_dir);dom=CompositionDOM();dom.feed((p/'index.html').read_text())
    audio=[a for tag,a in dom.media if tag=='audio']
    if len(audio)!=1:raise ValueError('Composition must have exactly one approved audio element')
    a=audio[0]
    if a.get('id')!='main-audio' or a.get('src')!='assets/narration.wav' or float(a.get('data-start',-1))!=0 or float(a.get('data-volume',1))!=1:
        raise ValueError('Composition must play the approved main audio from time zero at unity gain')
    if abs(float(a.get('data-duration',-1))-timeline['duration_seconds'])>.001 or float(a.get('data-media-start',0))!=0 or float(a.get('data-playback-rate',1))!=1:raise ValueError('Composition audio timing was changed')
    if any(tag=='video' and 'muted' not in attrs for tag,attrs in dom.media):raise ValueError('Visual video assets must be muted; narration is the only audible source')
    if set(dom.captions)!={f'caption-{i}' for i in range(len(timeline['captions']))}:raise ValueError('Composition caption set differs from the approved SRT')
    for i,c in enumerate(timeline['captions']):
        actual=dom.captions[f'caption-{i}'];attrs=actual['attrs']
        if actual['text'].strip()!=c['text']:raise ValueError('Composition caption text differs from the approved spoken words')
        start=float(attrs.get('data-start',-1));duration=float(attrs.get('data-duration',-1))
        if not all(math.isfinite(v) for v in (start,duration)) or abs(start-c['start'])>.001 or abs(start+duration-c['end'])>.001:raise ValueError('Composition caption timing differs from the approved SRT')
