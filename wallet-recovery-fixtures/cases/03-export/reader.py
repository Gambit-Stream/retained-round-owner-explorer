import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# This reader owns its contract; it does not import the fixture producer.
HEADERS = {
    'accounts.csv': ['brand', 'player', 'currency', 'opening', 'closing'],
    'events.csv': ['event', 'brand', 'player', 'currency', 'amount', 'time'],
    'exceptions.csv': ['exception', 'brand', 'player', 'currency', 'event', 'state'],
}


def key(row):
    return tuple(row[k] for k in ['brand', 'player', 'currency'])


def minor(value):
    if not re.fullmatch(r'-?(0|[1-9][0-9]*)', value):
        raise ValueError('INVALID_MINOR_UNITS')
    return int(value)


def read(root):
    root = Path(root)
    findings = []
    result = {'status': 'INCOMPLETE', 'findings': findings, 'histories': [],
              'exceptions': [], 'retry_authorized': False, 'source_authenticated': False}
    try:
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        if (manifest['schema'] != 'pam-history-demo/1'
                or manifest['synthetic'] is not True):
            raise ValueError('UNSUPPORTED_CONTRACT')
        if set(manifest['files']) != set(HEADERS):
            raise ValueError('FILE_INVENTORY_MISMATCH')
        tables = {}
        for name, headers in HEADERS.items():
            raw = (root / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != manifest['files'][name]['sha256']:
                raise ValueError('HASH_MISMATCH:' + name)
            with (root / name).open(newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != headers:
                    raise ValueError('HEADER_MISMATCH:' + name)
                rows = list(reader)
            if len(rows) != manifest['files'][name]['rows']:
                raise ValueError('ROW_COUNT_MISMATCH:' + name)
            if any(set(r) != set(headers) or any(not v for v in r.values()) for r in rows):
                raise ValueError('EMPTY_OR_EXTRA_FIELD:' + name)
            tables[name] = rows
        accounts = {}
        for row in tables['accounts.csv']:
            k = key(row)
            if k in accounts:
                raise ValueError('DUPLICATE_ACCOUNT')
            accounts[k] = (minor(row['opening']), minor(row['closing']))
        events = {}
        for row in tables['events.csv']:
            event = row['event']
            if event in events:
                raise ValueError('DUPLICATE_EVENT')
            timestamp = datetime.fromisoformat(row['time'])
            if timestamp.utcoffset() is None:
                raise ValueError('NAIVE_TIMESTAMP')
            minor(row['amount'])
            events[event] = row
            if key(row) not in accounts:
                findings.append('ORPHAN_EVENT:' + event)
            if manifest['event_owners'].get(event) != list(key(row)):
                findings.append('OWNER_MISMATCH:' + event)
        for event in sorted(set(manifest['event_owners']) - set(events)):
            findings.append('MISSING_EVENT:' + event)
        exception_ids = set()
        for row in tables['exceptions.csv']:
            ident = row['exception']
            if ident in exception_ids:
                raise ValueError('DUPLICATE_EXCEPTION')
            exception_ids.add(ident)
            if row['state'] not in ['UNRESOLVED', 'RECORDED']:
                raise ValueError('UNKNOWN_EXCEPTION_STATE')
            result['exceptions'].append(dict(row))
            if key(row) not in accounts:
                findings.append('ORPHAN_EXCEPTION:' + ident)
            referenced = events.get(row['event'])
            if referenced is None:
                findings.append('MISSING_REFERENCED_EVENT:' + ident)
            elif key(referenced) != key(row):
                findings.append('EXCEPTION_OWNER_MISMATCH:' + ident)
        for k, (opening, closing) in sorted(accounts.items()):
            selected = sorted((e for e in events.values() if key(e) == k),
                              key=lambda e: (datetime.fromisoformat(e['time']), e['event']))
            computed = opening + sum(minor(e['amount']) for e in selected)
            result['histories'].append({'account': list(k),
                'events': [e['event'] for e in selected], 'computed': computed,
                'declared': closing})
            if computed != closing:
                findings.append('BALANCE_MISMATCH:' + '/'.join(k))
        if not findings:
            result['status'] = ('READABLE_WITH_UNRESOLVED' if any(
                e['state'] == 'UNRESOLVED' for e in result['exceptions']) else 'READABLE')
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError) as exc:
        findings.append('INVALID_PACKAGE:' + str(exc))
    return result


if __name__ == '__main__':
    report = read(sys.argv[1])
    print(json.dumps(report, indent=2, sort_keys=True))
    sys.exit(2 if report['status'] == 'INCOMPLETE' else 0)
