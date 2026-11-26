"""Nine observable contracts for a synthetic positive-credit model."""
import os
import unittest
from dataclasses import replace
from settlement import Settlement


class SettlementContract(unittest.TestCase):
    def setUp(self):
        import settlement
        variant = os.environ.get('MODEL_VARIANT', 'Router')
        self.model = getattr(settlement, variant)('A')
        self.owner = self.model.create('local-1', 'round-17', 'alice', 'EUR')
        self.event = Settlement('A', 'round-17', 'local-1', 'event-1',
                                'alice', 'EUR', 500)

    def total(self):
        return sum(effect.settlement.amount_minor for effect in self.model.effects)

    def test_old_event_after_switch_credits_retained_owner(self):
        self.model.switch('B')
        self.assertEqual(self.model.callback(self.event), 'APPLIED')
        self.assertEqual(self.model.owners['local-1'], self.owner)
        self.assertEqual(self.model.effects[0].owner, self.owner)
        self.assertEqual(self.model.effects[0].settlement, self.event)
        self.assertEqual((len(self.model.effects), self.total()), (1, 500))
        self.assertEqual(self.model.callback_journal[-1].disposition, 'APPLIED')

    def test_new_round_uses_B_and_provider_scoped_ids_coexist(self):
        self.model.callback(self.event)
        self.model.switch('B')
        new = self.model.create('local-2', 'round-17', 'alice', 'EUR')
        self.assertEqual((new.provider, new.route_revision), ('B', 2))
        self.assertEqual(self.model.route_journal, [(1, 'A'), (2, 'B')])
        self.assertEqual(new.provider_round_id, self.owner.provider_round_id)
        event_b = replace(self.event, provider='B', local_round_id='local-2')
        self.assertEqual(self.model.callback(event_b), 'APPLIED')
        self.assertEqual([effect.owner for effect in self.model.effects],
                         [self.owner, new])
        self.assertEqual((len(self.model.effects), self.total()), (2, 1000))
        self.assertEqual(self.model.events[('A', 'event-1')], self.event)
        self.assertEqual(self.model.events[('B', 'event-1')], event_b)

    def test_duplicate_once_but_distinct_event_adds_credit(self):
        self.assertEqual(self.model.callback(self.event), 'APPLIED')
        self.assertEqual(self.model.callback(self.event), 'DUPLICATE')
        self.assertEqual((len(self.model.effects), self.total()), (1, 500))
        second = replace(self.event, event_id='event-2', amount_minor=250)
        self.assertEqual(self.model.callback(second), 'APPLIED')
        self.assertEqual((len(self.model.effects), self.total()), (2, 750))
        self.assertEqual([entry.disposition for entry in self.model.callback_journal],
                         ['APPLIED', 'DUPLICATE', 'APPLIED'])

    def test_changed_amount_conflicts_and_retains_first_meaning(self):
        self.model.callback(self.event)
        changed = replace(self.event, amount_minor=900)
        self.assertEqual(self.model.callback(changed), 'EVENT_CONFLICT')
        self.assertEqual(self.model.events[('A', 'event-1')], self.event)
        self.assertEqual(self.model.effects[0].settlement, self.event)
        self.assertEqual((len(self.model.effects), self.total()), (1, 500))
        self.assertEqual(self.model.callback_journal[-1].settlement, changed)
        self.assertEqual(self.model.callback_journal[-1].disposition, 'EVENT_CONFLICT')

    def assert_quarantined(self, candidate):
        self.assertEqual(self.model.callback(candidate), 'QUARANTINED')
        self.assertEqual(self.model.effects, [])
        self.assertEqual(self.model.owners, {'local-1': self.owner})
        self.assertEqual(self.model.callback_journal[-1].settlement, candidate)
        self.assertEqual(self.model.callback_journal[-1].disposition, 'QUARANTINED')

    def test_unknown_local_round_is_quarantined(self):
        self.assert_quarantined(replace(self.event, local_round_id='unknown'))

    def test_B_label_against_old_A_round_is_quarantined(self):
        self.model.switch('B')
        self.assert_quarantined(replace(self.event, provider='B'))

    def test_wrong_currency_is_quarantined(self):
        self.assert_quarantined(replace(self.event, currency='USD'))

    def test_wrong_player_is_quarantined(self):
        self.assert_quarantined(replace(self.event, player='bob'))

    def test_unavailable_old_route_holds_until_explicit_retry(self):
        self.model.switch('B')
        self.model.available['A'] = False
        self.assertEqual(self.model.callback(self.event), 'UNRESOLVED_OLD_ROUTE')
        self.assertEqual(self.model.held[('A', 'event-1')], self.event)
        self.assertEqual(self.model.effects, [])
        self.assertEqual(self.model.callback(self.event), 'UNRESOLVED_OLD_ROUTE')
        self.model.available['A'] = True
        self.assertEqual(self.model.callback(self.event), 'UNRESOLVED_OLD_ROUTE')
        self.assertEqual(self.model.effects, [])
        self.assertEqual(self.model.retry_held('A', 'event-1'), 'APPLIED')
        self.assertNotIn(('A', 'event-1'), self.model.held)
        self.assertEqual(self.model.effects[0].owner, self.owner)
        self.assertEqual(self.model.effects[0].settlement, self.event)
        self.assertEqual((len(self.model.effects), self.total()), (1, 500))
        self.assertEqual(self.model.callback(self.event), 'DUPLICATE')
        self.assertEqual((len(self.model.effects), self.total()), (1, 500))
        self.assertEqual([entry.disposition for entry in self.model.callback_journal],
                         ['UNRESOLVED_OLD_ROUTE'] * 3 + ['APPLIED', 'DUPLICATE'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
