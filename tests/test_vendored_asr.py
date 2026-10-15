"""Network-free checks of the reused ASR boundary with authored service responses."""
import sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from vendor.clean_talking_video import transcribe as asr

def response(payload):
    r=Mock();r.json.return_value=payload;r.raise_for_status.return_value=None;return r
class VendoredAsrTests(unittest.TestCase):
    def settings(self):return asr.DashScopeSettings(base_url='https://example.invalid',api_key='mock',model='mock',language='zh',poll_seconds=.5,timeout_seconds=30)
    def test_word_timestamps_requested_and_results_downloaded(self):
        session=Mock();session.post.return_value=response({'output':{'task_id':'fixture'}})
        payload={'transcripts':[{'sentences':[]}]}
        session.get.side_effect=[response({'output':{'task_status':'SUCCEEDED','transcription_url':'https://example.invalid/result'}}),response(payload)]
        with patch.object(asr,'upload_to_dashscope_temporary',return_value='oss://synthetic'):
            self.assertEqual(asr.transcribe_dashscope_task(Path('synthetic.ogg'),settings=self.settings(),prompt='',session=session),payload)
        self.assertTrue(session.post.call_args.kwargs['json']['parameters']['enable_words'])
    def test_failed_task_does_not_download_result(self):
        session=Mock();session.post.return_value=response({'output':{'task_id':'fixture'}});session.get.return_value=response({'output':{'task_status':'FAILED','message':'synthetic failure'}})
        with patch.object(asr,'upload_to_dashscope_temporary',return_value='oss://synthetic'):
            with self.assertRaisesRegex(RuntimeError,'FAILED'):asr.transcribe_dashscope_task(Path('synthetic.ogg'),settings=self.settings(),prompt='',session=session)
        self.assertEqual(session.get.call_count,1)
    def test_http_error_never_echoes_service_body(self):
        reply=response({});reply.status_code=401;reply.text='Bearer synthetic-secret https://signed.invalid/?token=private'
        reply.raise_for_status.side_effect=RuntimeError('synthetic-secret')
        with self.assertRaises(RuntimeError) as error:asr._check_response(reply,stage='task submission')
        self.assertIn('HTTP 401',str(error.exception));self.assertNotIn('synthetic-secret',str(error.exception));self.assertNotIn('signed.invalid',str(error.exception))
if __name__=='__main__':unittest.main()
