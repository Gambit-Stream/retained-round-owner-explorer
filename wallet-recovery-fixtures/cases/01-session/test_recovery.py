"""Seven observable requirements; identical suite for buggy and fixed frames."""
import os
import unittest
from dataclasses import replace

from recovery import (
    UNKNOWN, BuggyFrame, Intent, IntentConflict, SessionExpired,
    SessionRegistry, Wallet, WrongPlayer,
)


class RecoveryContract(unittest.TestCase):
    def setUp(self):
        import recovery
        self.frame_type = getattr(recovery, os.environ.get('FRAME_VARIANT', 'BuggyFrame'))
        self.sessions = SessionRegistry()
        self.old = self.sessions.issue('alice')
        self.wallet = Wallet(self.sessions, {'alice': 1000, 'bob': 1000})
        self.intent = Intent('alice', 'operation-1', 'ticket-7', 300, 'USD')
        self.frame = self.frame_type(self.wallet, self.old)

    def lose_reply(self):
        self.assertEqual(self.frame.place(self.intent, lose_reply=True), UNKNOWN)
        return self.sessions.issue('alice')

    def test_accepted_lost_reply_recovers_original_outcome_once(self):
        new = self.lose_reply()
        result = self.frame.reconnect(new)
        self.assertEqual(result.operation_id, self.intent.operation_id)
        self.assertEqual(result.status, 'ACCEPTED')
        self.assertEqual(result.response, 'accepted:operation-1')
        self.assertEqual(self.wallet.balances['alice'], 700)
        self.assertEqual(len(self.wallet.effects), 1)
        self.assertEqual(self.frame.reconnect(new), result)
        self.assertEqual(self.wallet.balances['alice'], 700)
        self.assertEqual(len(self.wallet.effects), 1)

    def test_retained_rejection_survives_replenishment(self):
        self.wallet.balances['alice'] = 100
        new = self.lose_reply()
        self.wallet.balances['alice'] = 1000
        result = self.frame.reconnect(new)
        self.assertEqual(result.operation_id, 'operation-1')
        self.assertEqual(result.status, 'REJECTED')
        self.assertEqual(result.response, 'rejected:operation-1')
        self.assertEqual(self.wallet.balances['alice'], 1000)
        self.assertEqual(self.wallet.effects, [])

    def test_unavailable_lookup_remains_unknown(self):
        new = self.lose_reply()
        self.wallet.lookup_available = False
        self.assertEqual(self.frame.reconnect(new), UNKNOWN)
        self.assertEqual(self.wallet.balances['alice'], 700)
        self.assertEqual(len(self.wallet.effects), 1)

    def test_missing_journal_does_not_create_operation(self):
        new = self.lose_reply()
        self.wallet.journal.clear()  # deterministic fault injection, not a real store
        self.assertEqual(self.frame.reconnect(new), UNKNOWN)
        self.assertEqual(self.wallet.balances['alice'], 700)
        self.assertEqual(len(self.wallet.effects), 1)
        self.assertEqual(self.wallet.journal, {})

    def test_wrong_player_recovery_is_denied(self):
        self.lose_reply()
        bob = self.sessions.issue('bob')
        with self.assertRaises(WrongPlayer):
            self.frame.reconnect(bob)
        self.assertEqual(self.wallet.balances, {'alice': 700, 'bob': 1000})
        self.assertEqual(len(self.wallet.effects), 1)

    def test_expired_session_is_denied(self):
        self.lose_reply()
        with self.assertRaises(SessionExpired):
            self.frame.reconnect(self.old)
        self.assertEqual(self.wallet.balances['alice'], 700)
        self.assertEqual(len(self.wallet.effects), 1)

    def test_operation_key_rejects_different_intent(self):
        original = self.wallet.submit(self.old, self.intent)
        with self.assertRaises(IntentConflict):
            self.wallet.submit(self.old, replace(self.intent, stake_minor=400))
        self.assertEqual(self.wallet.lookup(self.old, self.intent), original)
        self.assertEqual(self.wallet.balances['alice'], 700)
        self.assertEqual(len(self.wallet.effects), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
