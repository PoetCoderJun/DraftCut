"""ASR fragments must not change numbers or names in output captions."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from spoken_edit import canonical_transcript, joined

class TranscriptSpacingTests(unittest.TestCase):
    def words(self,text,tokens):
        value={'duration_seconds':len(tokens), 'segments':[{'start':0,'end':len(tokens),'text':text,
            'words':[{'start':i,'end':i+1,'text':t} for i,t in enumerate(tokens)]}]}
        return canonical_transcript(value,len(tokens))

    def test_numeric_and_acronym_fragments_keep_the_source_spelling(self):
        t,ws=self.words('晚上 11 点，AGI 与 POC。',['晚上','1','1','点，','AG','I','与','P','OC。'])
        self.assertEqual(joined(ws),'晚上 11 点，AGI 与 POC。')
        self.assertEqual(joined(ws[4:6]),'AGI')
        self.assertEqual(joined(ws[7:]),'POC。')
        self.assertEqual(joined(canonical_transcript(t,9)[1]),joined(ws))

    def test_distinct_english_words_keep_spaces(self):
        _,ws=self.words('OpenAI API supports 10 users.',['OpenAI','API','supports','1','0','users.'])
        self.assertEqual(joined(ws),'OpenAI API supports 10 users.')

    def test_unmatched_segment_text_does_not_invent_word_joins(self):
        _,ws=self.words('different recognition',['OpenAI','API'])
        self.assertEqual(joined(ws),'OpenAI API')

    def test_deletion_and_correction_keep_retained_word_separators(self):
        _,ws=self.words('old old AGI API',['old','old','AG','I','API'])
        kept=ws[1:];kept[-1]['text']='APIs'
        self.assertEqual(joined(kept),'old AGI APIs')

if __name__=='__main__':unittest.main()
