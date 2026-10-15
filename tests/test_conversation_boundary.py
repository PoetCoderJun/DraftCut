"""Cryptographic fixtures only; no authentic owner conversation adapter is available."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_approval import crypto, digest, issue, verify_receipt


class ConversationBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.passphrase = 'public-conversation-boundary-fixture'
        cls.keys = crypto('generate', {'passphrase': cls.passphrase})
        cls.other = crypto('generate', {'passphrase': cls.passphrase})

    def setUp(self):
        self.request = {'schema': 'draftcut.review-request.v2', 'stage': 'manuscript',
                        'project_id': 'fixture-project', 'generation': 1,
                        'subject': 'fixture-current-artifacts', 'review_sha256': 'fixture-review',
                        'example_only': False}

    def receipt(self):
        # A test authority supplied directly to this unit verifier, never OS owner trust.
        return issue(self.request, self.keys['private_key'], self.passphrase)

    def test_plain_conversation_cannot_establish_owner_provenance(self):
        unverified = {'payload': {'schema': 'draftcut.owner-conversation.v1',
                                 'role': 'user', 'actor': 'owner', 'decision': 'approved',
                                 'reply': '这版可以，继续。', 'message_id': 'claimed-message',
                                 'request_sha256': digest(self.request)}}
        with self.assertRaisesRegex(ValueError, 'missing, forged or stale'):
            verify_receipt(self.request, unverified, self.keys['public_key'])

    def test_agent_cannot_self_approve_by_copying_all_owner_fields(self):
        receipt = self.receipt(); receipt['signature'] = ''
        receipt['payload'].update(actor='owner', owner_approval=True, reply='通过')
        with self.assertRaises(ValueError):
            verify_receipt(self.request, receipt, self.keys['public_key'])

    def test_simulated_user_signature_cannot_become_production_approval(self):
        receipt = self.receipt()
        receipt['payload'].update(schema='draftcut.simulated-user-approval.v1',
                                  actor='simulated-user', owner_approval=False)
        with self.assertRaisesRegex(ValueError, 'missing, forged or stale'):
            verify_receipt(self.request, receipt, self.keys['public_key'])

    def test_an_agent_selected_signer_cannot_replace_trusted_issuer(self):
        receipt = issue(self.request, self.other['private_key'], self.passphrase)
        with self.assertRaisesRegex(ValueError, 'trusted human reviewer'):
            verify_receipt(self.request, receipt, self.keys['public_key'])

    def test_old_confirmation_is_rejected_for_new_revision_or_stage(self):
        receipt = self.receipt()
        for changes in ({'generation': 2}, {'stage': 'director'}, {'review_sha256': 'revised-review'}):
            changed = {**self.request, **changes}
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'stale'):
                verify_receipt(changed, receipt, self.keys['public_key'])

    def test_existing_current_signed_receipt_still_verifies(self):
        receipt = self.receipt()
        self.assertEqual(verify_receipt(self.request, receipt, self.keys['public_key']), digest(receipt))


if __name__ == '__main__': unittest.main()
