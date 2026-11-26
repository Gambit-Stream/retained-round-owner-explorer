import os
import pathlib
import tempfile
import unittest
from cashout import Cashout, BrokenCashout, Offer, Conflict, LostReply

ENGINE = BrokenCashout if os.environ.get('NEGATIVE_CONTROL') == '1' else Cashout


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.temp.name) / 'cashout.sqlite3'
        self.now = 100
        self.engine = ENGINE(self.path, lambda: self.now)
        self.engine.offer('A', 'B', Offer(7, 730, 120))

    def tearDown(self):
        self.engine.close()
        self.temp.cleanup()

    def accepted(self):
        return self.engine.accept('A', 'B', 'K', 7)

    def test_lost_reply_recovers_original_revision_after_new_offer(self):
        with self.assertRaises(LostReply):
            self.engine.accept('A', 'B', 'K', 7, lose_reply=True)
        self.engine.offer('A', 'B', Offer(8, 690, 140))
        self.assertEqual(self.engine.recover('A', 'K'), self.engine.lookup('A', 'K'))
        self.assertEqual(self.engine.recover('A', 'K')['state'], 'ACCEPTED')
        self.assertEqual(self.engine.effect_rows(), [('A', 'B', 'K', 730)])

    def test_expiry_after_acceptance_does_not_reject_recovery(self):
        original = self.accepted()
        self.now = 120
        self.assertEqual(self.engine.recover('A', 'K'), original)

    def test_missing_current_offer_does_not_erase_acceptance(self):
        original = self.accepted()
        with self.engine.db:
            self.engine.db.execute('DELETE FROM offers')
        self.assertEqual(self.engine.recover('A', 'K'), original)

    def test_reopen_database_preserves_accepted_result_after_revision(self):
        original = self.accepted()
        self.engine.offer('A', 'B', Offer(8, 690, 140))
        self.engine.close()
        self.engine = ENGINE(self.path, lambda: self.now)
        self.assertEqual(self.engine.recover('A', 'K'), original)
        self.assertEqual(len(self.engine.effect_rows()), 1)

    def test_same_key_same_payload_replays_without_second_effect(self):
        original = self.accepted()
        self.assertEqual(self.accepted(), original)
        self.assertEqual(len(self.engine.effect_rows()), 1)

    def test_same_key_changed_revision_conflicts_without_effect(self):
        original = self.accepted()
        with self.assertRaises(Conflict):
            self.engine.accept('A', 'B', 'K', 8)
        self.assertEqual(self.engine.lookup('A', 'K'), original)
        self.assertEqual(len(self.engine.effect_rows()), 1)

    def test_new_key_after_acceptance_rejected_without_second_effect(self):
        self.accepted()
        self.engine.offer('A', 'B', Offer(8, 690, 140))
        result = self.engine.accept('A', 'B', 'K2', 8)
        self.assertEqual(result['reason'], 'ALREADY_ACCEPTED')
        self.assertEqual(len(self.engine.effect_rows()), 1)

    def test_expiry_boundary_rejects_and_one_tick_before_accepts(self):
        self.now = 120
        self.assertEqual(self.accepted()['reason'], 'EXPIRED')
        self.assertEqual(self.engine.effect_rows(), [])
        self.now = 119
        self.engine.offer('A', 'C', Offer(2, 10, 120))
        self.assertEqual(self.engine.accept('A', 'C', 'L', 2)['state'], 'ACCEPTED')

    def test_known_rejection_survives_new_offer(self):
        self.now = 120
        original = self.accepted()
        self.engine.offer('A', 'B', Offer(8, 690, 150))
        self.now = 121
        self.assertEqual(self.engine.recover('A', 'K'), original)
        self.assertEqual(self.accepted(), original)
        self.assertEqual(self.engine.effect_rows(), [])

    def test_unavailable_lookup_is_unknown_and_read_only(self):
        self.accepted()
        before = self.engine.effect_rows()
        self.assertEqual(self.engine.recover('A', 'K', available=False),
                         {'state': 'UNKNOWN', 'reason': 'LOOKUP_UNAVAILABLE'})
        self.assertEqual(self.engine.effect_rows(), before)

    def test_absent_and_wrong_account_lookup_are_unknown(self):
        self.accepted()
        self.assertEqual(self.engine.recover('X', 'K')['state'], 'UNKNOWN')
        self.assertEqual(self.engine.recover('A', 'missing')['state'], 'UNKNOWN')
        self.assertEqual(len(self.engine.effect_rows()), 1)

    def test_interruption_between_decision_and_effect_rolls_back(self):
        with self.assertRaises(RuntimeError):
            self.engine.accept('A', 'B', 'K', 7, fail_after_decision=True)
        self.assertEqual(self.engine.lookup('A', 'K')['state'], 'UNKNOWN')
        self.assertEqual(self.engine.effect_rows(), [])
        self.assertEqual(self.accepted()['state'], 'ACCEPTED')

    def test_stale_revision_is_rejected_without_effect(self):
        self.assertEqual(self.engine.accept('A', 'B', 'K', 6)['reason'], 'REVISION_MISMATCH')
        self.assertEqual(self.engine.effect_rows(), [])

    def test_no_offer_is_rejected_without_effect(self):
        self.assertEqual(self.engine.accept('A', 'absent', 'K', 7)['reason'], 'NO_OFFER')
        self.assertEqual(self.engine.effect_rows(), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
