"""Emit actual, deterministic accepted and rejected lost-reply traces."""
from dataclasses import asdict
import json

from recovery import BuggyFrame, Frame, Intent, SessionExpired, SessionRegistry, Wallet


def trace(frame_type, initial_balance):
    sessions = SessionRegistry()
    old = sessions.issue('alice')
    wallet = Wallet(sessions, {'alice': initial_balance})
    intent = Intent('alice', 'operation-1', 'ticket-7', 300, 'USD')
    frame = frame_type(wallet, old)
    steps = [{'event': 'initial_session', 'token': old}]
    result = frame.place(intent, lose_reply=True)
    steps.append({'event': 'lost_reply', 'frame_result': result,
                  'retained': asdict(wallet.journal[intent.operation_id][1]),
                  'balance': wallet.balances['alice'], 'effects': len(wallet.effects)})
    new = sessions.issue('alice')
    steps.append({'event': 'new_session', 'token': new})
    try:
        wallet.lookup(old, intent)
    except SessionExpired:
        steps.append({'event': 'old_session_lookup', 'error': 'SessionExpired'})
    if initial_balance == 100:
        wallet.balances['alice'] = 1000
        steps.append({'event': 'replenished', 'balance': 1000})
    result = frame.reconnect(new)
    steps.append({'event': 'reconnect', 'result': asdict(result),
                  'balance': wallet.balances['alice'], 'effects': len(wallet.effects)})
    original = wallet.lookup(new, intent)
    steps.append({'event': 'lookup_original', 'result': asdict(original),
                  'balance': wallet.balances['alice'], 'effects': len(wallet.effects)})
    return {'variant': frame_type.__name__, 'initial_balance': initial_balance,
            'steps': steps}


if __name__ == '__main__':
    print(json.dumps({'synthetic': True, 'runs': [trace(variant, balance)
          for balance in (1000, 100) for variant in (BuggyFrame, Frame)]}, indent=2))
