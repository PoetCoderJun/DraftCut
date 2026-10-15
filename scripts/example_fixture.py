"""Known, non-private test source. Tones represent authored words, not real ASR."""
import hashlib, io, json, math, wave
RATE=48000
TEXT=['嗯','我们','支持','支持','三十','不对','四十','个','用户','不是','四十','万','Kimi','很','很','重要']
def fixture():
    data=bytearray();words=[];cursor=0
    for i,text in enumerate(TEXT):
        gap=48000 if i==9 else 7200
        data.extend(b'\0\0'*gap);cursor+=gap
        start=cursor
        for j in range(12000):
            value=int(3000*math.sin(2*math.pi*(220+i*19)*j/RATE))
            data.extend(value.to_bytes(2,'little',signed=True))
        cursor+=12000;words.append({'start':start/RATE,'end':cursor/RATE,'text':text})
    data.extend(b'\0\0'*7200);cursor+=7200
    b=io.BytesIO()
    with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes(bytes(data))
    t={'duration_seconds':cursor/RATE,'segments':[{'start':words[0]['start'],'end':words[-1]['end'],'text':''.join(TEXT),'words':words}]}
    pcm24=b''.join((int.from_bytes(data[i:i+2],'little',signed=True)*256).to_bytes(3,'little',signed=True) for i in range(0,len(data),2))
    return b.getvalue(),t,hashlib.sha256(pcm24).hexdigest()
def assert_fixture(project,manifest,transcript):
    if manifest.get('has_video'):raise ValueError('Example approval cannot authorize arbitrary source video')
    _,t,pcm_hash=fixture()
    expected=[(w['start'],w['end'],w['text']) for s in t['segments'] for w in s['words']]
    actual=[(w['start'],w['end'],w['text']) for s in transcript['segments'] for w in s['words']]
    with wave.open(str(project/'normalized-source.wav'),'rb') as w:
        actual_pcm=hashlib.sha256(w.readframes(w.getnframes())).hexdigest()
    if expected!=actual or actual_pcm!=pcm_hash:raise ValueError('Example authority accepts only the known synthetic tone fixture, never real recordings')
