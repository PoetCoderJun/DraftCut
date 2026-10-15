"""Missing production configuration is exercised entirely with a temporary trust path."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import spoken_workflow as workflow


class FirstRunApproval(unittest.TestCase):
    def test_missing_identity_has_an_owner_action_and_does_not_create_one(self):
        with tempfile.TemporaryDirectory() as folder:
            trust = Path(folder) / 'owner-config' / 'reviewer-public.pem'
            project = Path(folder) / 'project'
            with patch.object(workflow, 'TRUST_FILE', trust), patch.object(workflow, 'source_state', return_value=({}, {}, [])):
                with self.assertRaises(workflow.ApprovalRequired) as error:
                    workflow.project_trust(project)
            self.assertIn('setup yourself, outside the Agent', str(error.exception))
            self.assertFalse(trust.parent.exists())

    def test_a_project_local_public_key_cannot_be_production_trust(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder); trust = project / 'reviewer-public.pem'; trust.write_text('fixture')
            with patch.object(workflow, 'TRUST_FILE', trust), patch.object(workflow, 'source_state', return_value=({}, {}, [])):
                with self.assertRaisesRegex(ValueError, 'outside the editable project'):
                    workflow.project_trust(project)


if __name__ == '__main__': unittest.main()
