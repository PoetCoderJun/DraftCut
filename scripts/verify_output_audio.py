"""Check the exported AAC decodes to the approved original-voice timeline."""
import array,json,math,subprocess,tempfile
from pathlib import Path

def compare_audio(reference,output,sample_rate=48000):
    with tempfile.TemporaryDirectory(prefix='draftcut-audio-check-') as d:
        files=[]
        layouts=[]
        for source in (reference,output):
            metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_entries','stream=channels','-of','json',str(source)],text=True))
            layouts.append(int(metadata['streams'][0]['channels']))
        channels=layouts[1]
        if any(n not in (1,2) for n in layouts):raise ValueError('Waveform verification requires an explicitly prepared mono or stereo master')
        for i,source in enumerate((reference,output)):
            target=Path(d)/f'{i}.f32'
            mapping=[]
            if layouts[i]==1 and channels==2:mapping=['-af','pan=stereo|c0=c0|c1=c0']
            elif layouts[i]==2 and channels==1:mapping=['-af','pan=mono|c0=0.5*c0+0.5*c1']
            subprocess.run(['ffmpeg','-v','error','-xerror','-n','-i',str(source),'-map','0:a:0',*mapping,'-ac',str(channels),'-ar',str(sample_rate),'-f','f32le',str(target)],check=True,capture_output=True)
            files.append(target)
        expected=files[0].stat().st_size//4;actual=files[1].stat().st_size//4
        if abs(actual-expected)>2048*channels:raise ValueError('Exported audio duration differs by more than AAC padding')
        dot=e1=e2=diff=0.;count=0
        with files[0].open('rb') as left,files[1].open('rb') as right:
            while True:
                a=array.array('f');b=array.array('f');a.frombytes(left.read(65536));b.frombytes(right.read(65536))
                if not a or not b:break
                for x,y in zip(a,b):dot+=x*y;e1+=x*x;e2+=y*y;diff+=(x-y)**2;count+=1
        if not count:raise ValueError('Export has no decodable audio samples')
        cosine=dot/math.sqrt(e1*e2) if e1*e2 else 1. if e1==e2 else 0.
        normalized_error=diff/max(e1,1e-12)
        if cosine<.97 or normalized_error>.08:raise ValueError('Exported sound does not match the approved original-voice audio timeline')
        return {'scope':'decoded waveform comparison; not semantic/listening certification','channels':channels,'compared_samples':count,'expected_samples':expected,'actual_samples':actual,'cosine':cosine,'normalized_squared_error':normalized_error}
