# Retained-round owner explorer, 2026-11-11.1

Authored educational model. It does not connect to a provider or wallet, authenticate a callback, certify readiness or authorize an effect. Inputs are fictional selections only. No record upload, free-text credentials, analytics, persistence or API calls.

Input has exactly six enum fields: authenticity (verified/unverified), mapping (matched/missing/conflict/wrong-operator/expired), originalHandler (available/unavailable), result (unresolved/recorded), payload (same/changed), reviewer (assigned/unassigned). Reject any missing/extra key or unknown value. These are declared scenario assumptions, not checks against real systems.

Every report carries schema/rule versions, synthetic=true, operator OP-41, provider P-41, round R-41, event E-41, original handler Gateway A, new-round default Gateway B, record mapping-v7 and receipt receipt-41. A mapping reference is illustrative, not a hash or verified evidence. All reports state walletEffectAuthorized=false and liveChecks=0. No state permits a wallet call.

Evaluate ordered gates: unverified authenticity -> HOLD_AUTHENTICITY; mapping not matched -> HOLD_MAPPING; changed payload -> HOLD_PAYLOAD; original unavailable -> HOLD_ORIGINAL_HANDLER; otherwise recorded result -> REVIEW_RECORDED_RESULT, unresolved -> RECONCILE_ORIGINAL_RESULT. Only valid matched mappings expose candidateOwner Gateway A. New-round default never substitutes for retained owner. All missing gates remain recorded, including reviewer missing, even if an earlier gate determined the primary status. Reviewer missing never silently invents an assignee. Export reports are exact current selections with deterministic JSON and CSV, no timestamps or mutable identifiers.

Readiness is never approved. A matched record identifies an accountable review path only. Recorded result is an assumption of a lookup result, not proof of settlement or permission to replay. Retention and exact identity scope depend on actual provider/wallet contracts. This model selects operator+provider+round as a proposed scope; it is not a universal uniqueness guarantee.

Local tests must cover all gate branches, multi-gap preservation, exact validation, all 160 combinations, no effect authority, input immutability, deterministic exports and CSV field preservation. Browser checks cover selection, report changes, download, reset, no script errors and desktop/mobile overflow. Repository must include only newly authored files and the official public logo. Private research stays local.
