"""Conversational approvals stay simple while remaining revision-bound."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from spoken_workflow import digest, record_approval, verify_conversation_approval


class ConversationBoundary(unittest.TestCase):
    def setUp(self):
        self.request = {'schema': 'draftcut.review-request.v2', 'stage': 'manuscript',
                        'project_id': 'fixture-project', 'project_dir': '/fixture/project',
                        'generation': 1, 'subject': 'fixture-current-artifacts',
                        'review_sha256': 'fixture-review', 'example_only': False}

    def receipt(self):
        return {'payload': {'schema': 'draftcut.conversation-approval.v1',
                            'request_sha256': digest(self.request), 'stage': 'manuscript',
                            'project_id': 'fixture-project', 'generation': 1,
                            'decision': 'approved', 'source': 'direct-user-conversation',
                            'reply': '这版可以，继续。', 'recorded_at': 'fixture'}}

    def test_current_explicit_reply_is_accepted_without_a_signature(self):
        self.assertEqual(verify_conversation_approval(self.request, self.receipt()), digest(self.receipt()))

    def test_empty_or_wrong_source_is_rejected(self):
        for changes in ({'reply': ''}, {'source': 'synthetic-fixture'}):
            receipt = self.receipt(); receipt['payload'].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                verify_conversation_approval(self.request, receipt)

    def test_old_confirmation_is_rejected_for_new_revision_or_stage(self):
        for changes in ({'generation': 2}, {'stage': 'director'}, {'review_sha256': 'revised-review'}):
            changed = {**self.request, **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                verify_conversation_approval(changed, self.receipt())

    def test_recording_requires_the_current_sealed_request(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'request.json';path.write_text(json.dumps(self.request))
            with patch('spoken_workflow.validate_request') as validate:
                output = record_approval(path, '明确批准当前稿件')
            validate.assert_called_once()
            self.assertTrue(output.is_file())
            self.assertEqual(json.loads(output.read_text())['payload']['reply'], '明确批准当前稿件')


if __name__ == '__main__': unittest.main()
