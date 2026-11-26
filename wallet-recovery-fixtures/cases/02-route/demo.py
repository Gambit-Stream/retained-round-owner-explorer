"""Execute the invented ownership and explicit recovery scenarios."""
from dataclasses import asdict, replace
import json
from settlement import BuggyRouter, Router, Settlement


def setup(model_type):
    model = model_type('A')
    owner = model.create('local-1', 'round-17', 'alice', 'EUR')
    model.switch('B')
    event = Settlement('A', 'round-17', 'local-1', 'event-1',
                       'alice', 'EUR', 500)
    return model, owner, event


def snapshot(model, action, disposition):
    return {'action': action, 'disposition': disposition,
            'effect_count': len(model.effects),
            'total_minor': sum(x.settlement.amount_minor for x in model.effects),
            'held': [asdict(x) for x in model.held.values()]}


def ownership(model_type):
    model, owner, event = setup(model_type)
    steps = [snapshot(model, 'late_A', model.callback(event))]
    steps.append(snapshot(model, 'wrong_B_label',
                          model.callback(replace(event, provider='B'))))
    return {'variant': model_type.__name__, 'original_owner': asdict(owner),
            'route_journal': model.route_journal, 'steps': steps,
            'credit_effect_journal': [asdict(x) for x in model.effects],
            'callback_journal': [asdict(x) for x in model.callback_journal]}


def recovery():
    model, owner, event = setup(Router)
    model.available['A'] = False
    steps = [snapshot(model, 'A_unavailable', model.callback(event))]
    steps.append(snapshot(model, 'held_redelivery', model.callback(event)))
    model.available['A'] = True
    steps.append(snapshot(model, 'A_available_redelivery', model.callback(event)))
    steps.append(snapshot(model, 'explicit_retry_A_event_1',
                          model.retry_held('A', 'event-1')))
    steps.append(snapshot(model, 'redelivery_after_retry', model.callback(event)))
    return {'variant': 'Router', 'original_owner': asdict(owner),
            'route_journal': model.route_journal, 'steps': steps,
            'credit_effect_journal': [asdict(x) for x in model.effects],
            'callback_journal': [asdict(x) for x in model.callback_journal]}


if __name__ == '__main__':
    print(json.dumps({'synthetic': True,
                      'ownership_comparison': [ownership(BuggyRouter), ownership(Router)],
                      'explicit_recovery': recovery()}, indent=2))
