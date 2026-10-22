import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('experiment', Path(__file__).parents[1] / 'experiment.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        m.dataset(self.root / 'data', self.root / 'private')
        cfg = {k: 'test-value' for k in ['model', 'model_parameters', 'prompt_version', 'tool_version', 'schema_version', 'index_snapshot']}
        m.write(self.root / 'config.json', cfg)
        (self.root / 'prompt.txt').write_text('test prompt')
        self.f = m.freeze(self.root / 'data', self.root / 'config.json', [self.root / 'prompt.txt'], self.root / 'freeze.json')
    def run_fixture(self, name):
        p = self.root / name
        p.mkdir()
        rows = []
        for s in m.SOURCES:
            for tool, req in [('search_events', {'op': 'search', 'index': s, 'body': {'query': {'match_all': {}}}}), ('fetch_evidence', {'op': 'mget', 'index': s, 'body': {'ids': ['same-id']}})]:
                q = {'request': req}
                rows.append({'seq': len(rows)+1, 'run_id': name, 'tool': tool, 'status': 'ok', 'query': q,
                             'query_hash': m.digest(q), 'doc_ids': ['same-id'], 'result_count': 1, 'duration_ms': 10})
        (p / 'ledger.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        report = {'run_id': name, 'freeze_id': self.f['freeze_id'], 'verdict': 'confirmed',
            'claims': [{'id': 'c1', 'statement': 'fixture fact', 'citations': [{'index': 'windows-security', 'doc_id': 'same-id', 'ledger_seq': 2}]}],
            'source_coverage': {s: {'collector_complete': True, 'start': '2026-10-22T13:55:00+08:00', 'end': '2026-10-22T14:35:00+08:00'} for s in m.SOURCES}}
        m.write(p / 'report.json', report)
        return p
    def test_deterministic_dataset(self):
        m.dataset(self.root / 'other', self.root / 'private2')
        for p in (self.root / 'data').iterdir():
            self.assertEqual(p.read_bytes(), (self.root / 'other' / p.name).read_bytes())
    def test_mapping_compatible(self):
        template = m.read(Path(__file__).parents[2] / 'm1-elk/index_template.json')['template']['mappings']
        def validate(doc, mapping):
            for k, v in doc.items():
                self.assertIn(k, mapping['properties'])
                if isinstance(v, dict): validate(v, mapping['properties'][k])
        for p in (self.root / 'data').glob('*.ndjson'):
            if p.name == 'bulk.ndjson': continue
            for line in p.read_text().splitlines(): validate(json.loads(line)['_source'], template)
    def test_private_separation(self):
        with self.assertRaises(ValueError): m.dataset(self.root/'data', self.root/'data'/'private')
    def test_identical_and_index_qualified(self):
        a, b = self.run_fixture('a'), self.run_fixture('b')
        r = m.compare(a, b, self.root/'freeze.json')
        self.assertEqual(r['query_jaccard'], 1)
        self.assertEqual(len(m.evaluate(a, self.f)['_evidence']), 3)
        self.assertEqual(r['runs'][0]['citation_reference_coverage'], 1)
    def test_missing_citation_and_coverage(self):
        p = self.run_fixture('a'); r = m.read(p/'report.json')
        r['claims'][0]['citations'][0]['ledger_seq'] = 1
        r['source_coverage']['zeek']['collector_complete'] = False
        m.write(p/'report.json', r)
        e = m.evaluate(p, self.f)
        self.assertEqual(e['citation_reference_coverage'], 0)
        self.assertFalse(e['time_window_coverage_declared']['zeek'])
    def test_changes_and_empty_sets(self):
        self.assertIsNone(m.overlap(set(), set()))
        self.assertNotEqual(m.normalize({'size': 1}), m.normalize({'size': 2}))
        self.assertEqual(m.normalize({'a': 1, 'b': 2}), m.normalize({'b': 2, 'a': 1}))
    def test_tampered_ledger(self):
        p = self.run_fixture('a')
        rows = [json.loads(s) for s in (p/'ledger.jsonl').read_text().splitlines()]
        rows[0]['query']['request']['index'] = 'forbidden'
        (p/'ledger.jsonl').write_text('\n'.join(json.dumps(r) for r in rows))
        with self.assertRaises(ValueError): m.evaluate(p, self.f)
    def test_mixed_run_and_invalid_verdict(self):
        p = self.run_fixture('a'); r = m.read(p/'report.json'); r['run_id'] = 'other'
        m.write(p/'report.json', r)
        with self.assertRaises(ValueError): m.evaluate(p, self.f)
    def test_manifest_tamper_and_same_run(self):
        p = self.run_fixture('a')
        with self.assertRaises(ValueError): m.compare(p, p, self.root/'freeze.json')
        f = copy.deepcopy(self.f); f['configuration']['model'] = 'changed'; m.write(self.root/'freeze.json', f)
        with self.assertRaises(ValueError): m.compare(p, p, self.root/'freeze.json')

if __name__ == '__main__': unittest.main()
