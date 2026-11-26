"""Synthetic single-connection decision model; no network or real money."""
from dataclasses import dataclass
import json
import sqlite3


@dataclass(frozen=True)
class Offer:
    revision: int
    units: int
    expires: int


class Conflict(Exception):
    pass


class LostReply(Exception):
    pass


class Cashout:
    def __init__(self, path, clock):
        self.clock = clock
        self.db = sqlite3.connect(path)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS offers (
          account TEXT, bet TEXT, revision INTEGER, units INTEGER,
          expires INTEGER, PRIMARY KEY(account, bet));
        CREATE TABLE IF NOT EXISTS decisions (
          account TEXT, request_key TEXT, fingerprint TEXT, body TEXT,
          PRIMARY KEY(account, request_key));
        CREATE TABLE IF NOT EXISTS effects (
          account TEXT, bet TEXT, request_key TEXT, units INTEGER,
          PRIMARY KEY(account, bet));
        ''')

    def close(self):
        self.db.close()

    def offer(self, account, bet, value):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO offers VALUES (?,?,?,?,?)',
                            (account, bet, value.revision, value.units, value.expires))

    def lookup(self, account, request_key, available=True):
        if not available:
            return {'state': 'UNKNOWN', 'reason': 'LOOKUP_UNAVAILABLE'}
        row = self.db.execute('SELECT body FROM decisions WHERE account=? AND request_key=?',
                              (account, request_key)).fetchone()
        return json.loads(row[0]) if row else {'state': 'UNKNOWN', 'reason': 'NO_RECORD'}

    def accept(self, account, bet, request_key, revision, lose_reply=False,
               fail_after_decision=False):
        fingerprint = json.dumps([bet, revision], separators=(',', ':'))
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            prior = self.db.execute(
                'SELECT fingerprint,body FROM decisions WHERE account=? AND request_key=?',
                (account, request_key)).fetchone()
            if prior:
                if prior[0] != fingerprint:
                    raise Conflict('Same account/key with different bet or revision')
                result = json.loads(prior[1])
            else:
                row = self.db.execute(
                    'SELECT revision,units,expires FROM offers WHERE account=? AND bet=?',
                    (account, bet)).fetchone()
                now = self.clock()
                claimed = self.db.execute('SELECT 1 FROM effects WHERE account=? AND bet=?',
                                           (account, bet)).fetchone()
                reason = ('ALREADY_ACCEPTED' if claimed else
                          'NO_OFFER' if row is None else
                          'REVISION_MISMATCH' if row[0] != revision else
                          'EXPIRED' if now >= row[2] else 'ACCEPTED')
                result = dict(state='ACCEPTED' if reason == 'ACCEPTED' else 'REJECTED',
                              reason=reason, account=account, bet=bet,
                              request_key=request_key, revision=revision,
                              decided_at=now, units=row[1] if reason == 'ACCEPTED' else 0)
                self.db.execute('INSERT INTO decisions VALUES (?,?,?,?)',
                                (account, request_key, fingerprint, json.dumps(result, sort_keys=True)))
                if fail_after_decision:
                    raise RuntimeError('Injected interruption before effect')
                if result['state'] == 'ACCEPTED':
                    self.db.execute('INSERT INTO effects VALUES (?,?,?,?)',
                                    (account, bet, request_key, result['units']))
        # The deliberate lost reply occurs AFTER the transaction commits.
        if lose_reply:
            raise LostReply('Committed decision; client did not receive reply')
        return result

    def recover(self, account, request_key, available=True):
        return self.lookup(account, request_key, available)

    def effect_rows(self):
        return self.db.execute('SELECT account,bet,request_key,units FROM effects ORDER BY account,bet').fetchall()


class BrokenCashout(Cashout):
    """Negative control: incorrectly rechecks current offer during recovery."""
    def recover(self, account, request_key, available=True):
        result = self.lookup(account, request_key, available)
        if result['state'] != 'ACCEPTED':
            return result
        row = self.db.execute('SELECT revision,expires FROM offers WHERE account=? AND bet=?',
                              (account, result['bet'])).fetchone()
        if row is None or row[0] != result['revision'] or self.clock() >= row[1]:
            return dict(result, state='REJECTED', reason='CURRENT_OFFER_INVALID')
        return result
