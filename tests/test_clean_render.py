import sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from render_clean import frame_allocations,render,validate_subtitles
from example_fixture import fixture
from spoken_edit import initialize,write

class CleanRenderTests(unittest.TestCase):
 def test_cumulative_rounding_does_not_accumulate_per_cut_error(self):
  segments=[{'source_start_sample':i*1000,'source_end_sample':i*1000+801,'output_start_sample':i*801} for i in range(100)]
  result=frame_allocations({'segments':segments},60)
  self.assertEqual(sum(x['frame_count'] for x in result),round(80100/48000*60))
  self.assertTrue(all(a['output_end_frame']==b['output_start_frame'] for a,b in zip(result,result[1:])))
 def test_subframe_cuts_are_rejected(self):
  with self.assertRaisesRegex(ValueError,'shorter than one'):
   frame_allocations({'segments':[{'source_start_sample':0,'source_end_sample':1,'output_start_sample':0}]},60)
 def test_empty_approval_note_cannot_start_an_export(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out'
   with self.assertRaisesRegex(ValueError,'actual user approval'):render(Path(d)/'missing',out,'hardware',' ')
   self.assertFalse(out.exists())
 def test_fixture_is_not_promoted_to_clean_production(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);audio,t,_=fixture();source=p/'source.wav';source.write_bytes(audio);write(p/'transcript.json',t)
   initialize(source,p/'transcript.json',p/'project',example_only=True)
   with self.assertRaisesRegex(ValueError,'fixtures or simulations'):render(p/'project',p/'out','hardware','Test note')
   self.assertFalse((p/'out').exists())
 def test_prior_output_is_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'out';out.mkdir();(out/'old.txt').write_text('keep')
   with self.assertRaisesRegex(ValueError,'preserve prior'):render(Path(d)/'missing',out,'hardware','Approved')
   self.assertEqual((out/'old.txt').read_text(),'keep')

 def test_subtitles_must_stay_inside_the_clean_timeline(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'final.srt';f.write_text('1\n00:00:00,100 --> 00:00:01,000\n完整表达\n')
   self.assertEqual(validate_subtitles(f,1),1)
   with self.assertRaisesRegex(ValueError,'outside'):validate_subtitles(f,.5)
 def test_overlapping_subtitles_are_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'final.srt';f.write_text('1\n00:00:00,100 --> 00:00:01,000\n一\n\n2\n00:00:00,900 --> 00:00:01,200\n二\n')
   with self.assertRaisesRegex(ValueError,'overlap'):validate_subtitles(f,2)

if __name__=='__main__':unittest.main()
