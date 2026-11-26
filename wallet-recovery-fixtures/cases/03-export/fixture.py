import csv
import hashlib
import json
from pathlib import Path

HEADERS = {
    'accounts.csv': ['brand', 'player', 'currency', 'opening', 'closing'],
    'events.csv': ['event', 'brand', 'player', 'currency', 'amount', 'time'],
    'exceptions.csv': ['exception', 'brand', 'player', 'currency', 'event', 'state'],
}


def write_rows(root, name, rows):
    with (root / name).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=HEADERS[name])
        w.writeheader()
        w.writerows(rows)


def seal(root):
    manifest = json.loads((root / 'manifest.json').read_text())
    manifest['files'] = {}
    for name in HEADERS:
        raw = (root / name).read_bytes()
        with (root / name).open(newline='', encoding='utf-8') as f:
            count = len(list(csv.DictReader(f)))
        manifest['files'][name] = {
            'sha256': hashlib.sha256(raw).hexdigest(), 'rows': count}
    (root / 'manifest.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


def make(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    accounts = [dict(zip(HEADERS['accounts.csv'], row)) for row in [
        ['B-A', 'P-301', 'EUR', '10000', '10300'],
        ['B-B', 'P-301', 'EUR', '20000', '20300']]]
    events = [dict(zip(HEADERS['events.csv'], row)) for row in [
        ['E-301', 'B-A', 'P-301', 'EUR', '500', '2026-11-01T10:00:00+00:00'],
        ['E-302', 'B-B', 'P-301', 'EUR', '500', '2026-11-01T10:01:00+00:00'],
        ['E-303', 'B-A', 'P-301', 'EUR', '-200', '2026-11-01T10:02:00+00:00'],
        ['E-304', 'B-B', 'P-301', 'EUR', '-200', '2026-11-01T10:03:00+00:00']]]
    exceptions = [dict(zip(HEADERS['exceptions.csv'],
        ['X-301', 'B-A', 'P-301', 'EUR', 'E-301', 'UNRESOLVED']))]
    for name, rows in zip(HEADERS, [accounts, events, exceptions]):
        write_rows(root, name, rows)
    manifest = {'schema': 'pam-history-demo/1', 'synthetic': True,
        'scope': 'Four invented events; not a complete player lifecycle',
        'event_owners': {e['event']: [e[k] for k in ['brand', 'player', 'currency']]
                         for e in events}}
    (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    seal(root)


if __name__ == '__main__':
    import sys
    make(sys.argv[1] if len(sys.argv) > 1 else 'export')
