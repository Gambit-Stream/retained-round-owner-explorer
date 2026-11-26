"""Synthetic in-memory wallet; no network, browser, persistence or real auth."""
from dataclasses import dataclass, replace

UNKNOWN = 'UNKNOWN'


class SessionExpired(Exception):
    pass


class WrongPlayer(Exception):
    pass


class IntentConflict(Exception):
    pass


class LostReply(Exception):
    pass


@dataclass(frozen=True)
class Intent:
    player: str
    operation_id: str
    ticket: str
    stake_minor: int
    currency: str


@dataclass(frozen=True)
class Outcome:
    operation_id: str
    status: str
    response: str


class SessionRegistry:
    def __init__(self):
        self.active = {}
        self.owners = {}
        self.sequence = 0

    def issue(self, player):
        self.sequence += 1
        token = f'session-{self.sequence}'
        self.active[player] = token
        self.owners[token] = player
        return token

    def check(self, token, player):
        owner = self.owners.get(token)
        if owner is None or self.active.get(owner) != token:
            raise SessionExpired(token)
        if owner != player:
            raise WrongPlayer(player)


class Wallet:
    def __init__(self, sessions, balances):
        self.sessions = sessions
        self.balances = dict(balances)
        self.journal = {}
        self.effects = []
        self.lookup_available = True

    def submit(self, session, intent, lose_reply=False):
        self.sessions.check(session, intent.player)
        retained = self.journal.get(intent.operation_id)
        if retained is not None:
            canonical, outcome = retained
            if canonical != intent:
                raise IntentConflict(intent.operation_id)
        else:
            accepted = self.balances[intent.player] >= intent.stake_minor
            status = 'ACCEPTED' if accepted else 'REJECTED'
            outcome = Outcome(intent.operation_id, status,
                              f'{status.lower()}:{intent.operation_id}')
            if accepted:
                self.balances[intent.player] -= intent.stake_minor
                self.effects.append(intent)
            self.journal[intent.operation_id] = (intent, outcome)
        if lose_reply:
            raise LostReply(intent.operation_id)
        return outcome

    def lookup(self, session, intent):
        self.sessions.check(session, intent.player)
        if not self.lookup_available:
            return UNKNOWN
        retained = self.journal.get(intent.operation_id)
        if retained is None:
            return UNKNOWN
        canonical, outcome = retained
        if canonical != intent:
            raise IntentConflict(intent.operation_id)
        return outcome


class BuggyFrame:
    def __init__(self, wallet, session):
        self.wallet, self.session = wallet, session
        self.intent = None

    def place(self, intent, lose_reply=False):
        self.intent = intent
        try:
            return self.wallet.submit(self.session, intent, lose_reply=lose_reply)
        except LostReply:
            return UNKNOWN

    def reconnect(self, new_session):
        self.wallet.sessions.check(new_session, self.intent.player)
        self.session = new_session
        replacement = replace(self.intent, operation_id=f'{new_session}:replacement')
        return self.wallet.submit(new_session, replacement)


class Frame(BuggyFrame):
    def reconnect(self, new_session):
        self.session = new_session
        return self.wallet.lookup(new_session, self.intent)
