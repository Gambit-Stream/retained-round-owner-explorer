"""Synthetic sequential positive credits; no real ledger or authentication."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RoundOwner:
    local_round_id: str
    provider: str
    provider_round_id: str
    player: str
    currency: str
    route_revision: int


@dataclass(frozen=True)
class Settlement:
    provider: str
    provider_round_id: str
    local_round_id: str
    event_id: str
    player: str
    currency: str
    amount_minor: int


@dataclass(frozen=True)
class Credit:
    owner: RoundOwner
    settlement: Settlement


@dataclass(frozen=True)
class CallbackRecord:
    settlement: Settlement
    disposition: str


class BuggyRouter:
    def __init__(self, provider):
        self.provider, self.revision = provider, 1
        self.route_journal = [(self.revision, provider)]
        self.available = {provider: True}
        self.owners = {}
        self.events = {}
        self.held = {}
        self.effects = []
        self.callback_journal = []

    def switch(self, provider):
        self.provider = provider
        self.revision += 1
        self.route_journal.append((self.revision, provider))
        self.available.setdefault(provider, True)

    def create(self, local_round_id, provider_round_id, player, currency):
        if local_round_id in self.owners:
            raise ValueError('local round already assigned')
        owner = RoundOwner(local_round_id, self.provider, provider_round_id,
                           player, currency, self.revision)
        self.owners[local_round_id] = owner
        return owner

    def provider_matches(self, owner, event):
        # Deliberate defect: use today's default as the historical owner.
        return event.provider == self.provider

    def record(self, event, disposition):
        self.callback_journal.append(CallbackRecord(event, disposition))
        return disposition

    def apply(self, event):
        owner = self.owners.get(event.local_round_id)
        if (owner is None or not self.provider_matches(owner, event) or
                (event.provider_round_id, event.local_round_id,
                 event.player, event.currency) !=
                (owner.provider_round_id, owner.local_round_id,
                 owner.player, owner.currency)):
            return self.record(event, 'QUARANTINED')
        key = (event.provider, event.event_id)
        if not self.available.get(owner.provider, False):
            self.held[key] = event
            return self.record(event, 'UNRESOLVED_OLD_ROUTE')
        self.effects.append(Credit(owner, event))
        self.held.pop(key, None)
        return self.record(event, 'APPLIED')

    def callback(self, event):
        if type(event.amount_minor) is not int or event.amount_minor <= 0:
            raise ValueError('positive integer minor units required')
        key = (event.provider, event.event_id)
        if key in self.events:
            if self.events[key] != event:
                disposition = 'EVENT_CONFLICT'
            elif key in self.held:
                disposition = 'UNRESOLVED_OLD_ROUTE'
            else:
                disposition = 'DUPLICATE'
            return self.record(event, disposition)
        self.events[key] = event
        return self.apply(event)

    def retry_held(self, provider, event_id):
        # Explicit retry accepts an event key, never a replacement payload.
        event = self.held[(provider, event_id)]
        return self.apply(event)


class Router(BuggyRouter):
    def provider_matches(self, owner, event):
        return event.provider == owner.provider
