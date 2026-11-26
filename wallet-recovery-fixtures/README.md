# iGaming Wallet Recovery Fixtures: Session, Route and Decision Contracts

Four original synthetic Python examples from Gambit Stream's published technical articles, packaged as separate cases. Run their unchanged tests through one standard-library runner. The observed corrected result is **46 passing test methods** across four independent subprocesses.

## Reproduce

From this directory, using Python 3 with the standard-library SQLite module:

```sh
python3 run.py
python3 run.py --verbose
```

The retained execution used CPython 3.14.7. Other Python versions and operating systems have not been verified. No installation or credentials are needed.

Stable stdout for the first command is in [expected-output.txt](expected-output.txt):

```text
01-session: PASS (7 tests)
02-route: PASS (9 tests)
03-export: PASS (16 tests)
04-decision: PASS (14 tests)
TOTAL: PASS (46 tests)
```

The runner copies each case into a fresh temporary directory, launches its own Python subprocess and removes that copy afterward. It selects corrected `Frame` and `Router` explicitly and removes ambient negative-control selectors. Python environment overrides are ignored. Original sources and packaged cases remain unchanged. A nonzero subprocess exit or an unexpected test count makes the runner fail.

## Case contracts and limits

| Directory | Tested contract | Boundary |
|---|---|---|
| [01-session](cases/01-session) | Reconnect looks up the original immutable operation; retained rejection stays rejected after replenishment; unavailable history stays `UNKNOWN`. Seven methods. | In-memory sequential model with integer USD minor units. Fake session registry; no browser, iframe SDK or durable journal. Default in the original test file is deliberately buggy; use the runner for the corrected variant. |
| [02-route](cases/02-route) | Late positive-credit events use the retained round owner; duplicates and changed payloads remain distinct; an unavailable old route requires explicit held-event retry. Nine methods. | In-memory sequential records. No money movement, signature validation or final-settlement semantics. Supported processing entry points are `callback` and `retry_held`; helper `apply` alone does not deduplicate. |
| [03-export](cases/03-export) | Reconstruct account histories with brand/player/currency ownership checks; expose malformed packages and unresolved exceptions. Sixteen methods. | Four invented events across two accounts. File hashes do not authenticate the source. `READABLE_WITH_UNRESOLVED` authorizes no retry and establishes no complete player lifecycle. |
| [04-decision](cases/04-decision) | Recover the retained cashout decision after an offer changes or expires; replay accepted requests without a second effect; roll back the injected interruption. Fourteen methods. | One local SQLite connection, simulated integer units and a supplied clock. A database reopen is tested; distributed durability and concurrent acceptance are untested. |

These fixtures make no production security, concurrency or performance claim. They call no network, provider or real wallet. They are examples to inspect, not deployment or financial advice.

[Gambit Stream sportsbook iframe integration scope](https://gambitstream.com/sportsbook-iframe/) gives commercial scope context. The fixtures are synthetic teaching examples and do not establish provider behavior.

## Sources and execution evidence

The four parent articles are:

- [Sportsbook iframe reconnects and the original wallet operation](https://dev.to/gambit_stream/sportsbook-iframe-integration-test-reconnects-against-the-original-wallet-operation-2i82)
- [Provider replacement and late settlements to the original round](https://dev.to/gambit_stream/casino-provider-replacement-route-late-settlements-to-the-original-round-10n6)
- [PAM export history reconstruction with 16 tests](https://dev.to/gambit_stream/pam-data-export-reconstruct-player-histories-with-16-tests-3im4)
- [Cashout decision recovery after client disconnect](https://dev.to/gambit_stream/sportsbook-cashout-recover-the-decision-after-the-client-disconnects-ael)

[provenance.json](provenance.json) pins each original module, test and retained input by source snapshot and SHA256. It distinguishes committed source matches from local retained snapshots; it does not claim a mutable article revision ID. [expected-results.json](expected-results.json) records commands, runtime and passing test names. The [evidence](evidence) directory contains actual test logs, two demo outputs and the export reader report. Test durations vary; compare status and method counts rather than log bytes.

## Reuse

This subdirectory inherits the repository's existing [MIT license](../LICENSE), copyright 2026 Gambit Stream. The included modules were prepared for the four cited tutorials; source snapshots and hashes are retained in provenance.json. No third-party code was copied for this package. The official logo is excluded; this directory contains no logo or image assets. No additional license grant or license change is introduced here.
