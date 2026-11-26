import csv
import json
import tempfile
import unittest
from pathlib import Path
from fixture import make, seal, write_rows
from reader import read


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        make(self.root)

    def rows(self, name):
        with (self.root / name).open(newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def change(self, name, rows):
        write_rows(self.root, name, rows)
        seal(self.root)  # Defects survive internally consistent file hashes.

    def has(self, code):
        report = read(self.root)
        self.assertEqual(report['status'], 'INCOMPLETE')
        self.assertTrue(any(code in f for f in report['findings']), report)
        return report

    def test_clean_matches_handwritten_oracle(self):
        r = read(self.root)
        self.assertEqual(r['status'], 'READABLE_WITH_UNRESOLVED')
        self.assertEqual(r['histories'], [
            {'account': ['B-A','P-301','EUR'], 'events': ['E-301','E-303'],
             'computed': 10300, 'declared': 10300},
            {'account': ['B-B','P-301','EUR'], 'events': ['E-302','E-304'],
             'computed': 20300, 'declared': 20300}])
        self.assertEqual(r['exceptions'][0]['state'], 'UNRESOLVED')
        self.assertFalse(r['retry_authorized'])

    def test_missing_event(self):
        self.change('events.csv', self.rows('events.csv')[1:])
        self.has('MISSING_REFERENCED_EVENT:X-301')

    def test_orphan_exception_stays_visible(self):
        rows = self.rows('exceptions.csv'); rows[0]['brand'] = 'B-MISSING'
        self.change('exceptions.csv', rows)
        self.assertEqual(len(self.has('ORPHAN_EXCEPTION')['exceptions']), 1)

    def test_equal_totals_wrong_owners(self):
        rows = self.rows('events.csv')
        rows[0]['brand'], rows[1]['brand'] = rows[1]['brand'], rows[0]['brand']
        self.change('events.csv', rows)
        r = self.has('OWNER_MISMATCH')
        self.assertTrue(all(h['computed'] == h['declared'] for h in r['histories']))

    def test_exception_points_to_other_owner(self):
        rows = self.rows('exceptions.csv'); rows[0]['event'] = 'E-302'
        self.change('exceptions.csv', rows); self.has('EXCEPTION_OWNER_MISMATCH')

    def test_duplicate_event(self):
        rows = self.rows('events.csv'); rows.append(rows[0])
        self.change('events.csv', rows); self.has('DUPLICATE_EVENT')

    def test_duplicate_account(self):
        rows = self.rows('accounts.csv'); rows.append(rows[0])
        self.change('accounts.csv', rows); self.has('DUPLICATE_ACCOUNT')

    def test_duplicate_exception(self):
        rows = self.rows('exceptions.csv'); rows.append(rows[0])
        self.change('exceptions.csv', rows); self.has('DUPLICATE_EXCEPTION')

    def test_hash_mismatch(self):
        with (self.root/'events.csv').open('a') as f: f.write('\n')
        self.has('HASH_MISMATCH')

    def test_schema_mismatch(self):
        p = self.root/'manifest.json'; m = json.loads(p.read_text())
        m['schema'] = 'pam-history-demo/2'; p.write_text(json.dumps(m))
        self.has('UNSUPPORTED_CONTRACT')

    def test_row_count(self):
        p = self.root/'manifest.json'; m = json.loads(p.read_text())
        m['files']['events.csv']['rows'] = 999; p.write_text(json.dumps(m))
        self.has('ROW_COUNT_MISMATCH')

    def test_missing_file(self):
        (self.root/'events.csv').unlink(); self.has('INVALID_PACKAGE')

    def test_naive_time(self):
        rows=self.rows('events.csv'); rows[0]['time']='2026-11-01T10:00:00'
        self.change('events.csv', rows); self.has('NAIVE_TIMESTAMP')

    def test_decimal_amount(self):
        rows=self.rows('events.csv'); rows[0]['amount']='5.00'
        self.change('events.csv', rows); self.has('INVALID_MINOR_UNITS')

    def test_balance_mismatch(self):
        rows=self.rows('accounts.csv'); rows[0]['closing']='10301'
        self.change('accounts.csv', rows); self.has('BALANCE_MISMATCH')

    def test_orphan_event(self):
        rows=self.rows('events.csv'); rows[0]['brand']='B-MISSING'
        self.change('events.csv', rows); self.has('ORPHAN_EVENT')


if __name__ == '__main__':
    unittest.main()
