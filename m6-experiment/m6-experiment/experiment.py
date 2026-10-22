#!/usr/bin/env python3
"""M6 offline experiment toolkit. Python 3.10+, standard library only."""
import argparse
import base64
import hashlib
import json
from datetime import datetime
from pathlib import Path

SOURCES = ['windows-security', 'sysmon', 'zeek']

def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def write(p, x):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def stamp(x):
    d = datetime.fromisoformat(x.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('timestamps must include timezone')
    return d.timestamp()

def dataset(public, private):
    """Generate fixtures, never execute the encoded command or send network traffic."""
    public, private = Path(public).resolve(), Path(private).resolve()
    if private == public or public in private.parents:
        raise ValueError('private directory must be outside public directory')
    events = {s: [] for s in SOURCES}
    relevant = []
    def add(s, minute, fields, target=False):
        n = len(events[s]) + 1
        eid = f'{s}-{n:03}'
        doc = {'@timestamp': f'2026-10-22T14:{minute}:00+08:00',
               'event': {'id': eid, 'dataset': s, 'kind': 'event'},
               'ecs': {'version': '8.11.0'}, 'host': {'name': 'WS-01'}, **fields}
        events[s].append({'_index': s, '_id': eid, '_source': doc})
        if target:
            relevant.append(f'{s}:{eid}')
        return doc
    for i in range(8):
        d = add('windows-security', f'{i:02}', {'user': {'name': 'lab-user'},
                'source': {'ip': '10.10.10.99'}, 'winlog': {'logon': {'type': 3}}}, True)
        d['event'].update(code='4625', outcome='failure')
    d = add('windows-security', '09', {'user': {'name': 'lab-user'},
            'source': {'ip': '10.10.10.99'}, 'winlog': {'logon': {'type': 3}}}, True)
    d['event'].update(code='4624', outcome='success')
    cmd = base64.b64encode("Write-Output 'TraceHunt lab marker'".encode('utf-16-le')).decode()
    d = add('sysmon', '12', {'user': {'name': 'lab-user'}, 'process': {
        'name': 'powershell.exe', 'pid': 4242, 'entity_id': 'lab-process-4242',
        'command_line': 'powershell.exe -NoProfile -EncodedCommand ' + cmd,
        'parent': {'name': 'cmd.exe', 'pid': 4000}}}, True)
    d['event']['code'] = '1'
    add('zeek', '14', {'source': {'ip': '10.10.10.21', 'port': 51000},
        'destination': {'ip': '10.10.10.50', 'port': 8080}, 'network': {'transport': 'tcp'},
        'url': {'original': 'http://10.10.10.50:8080/checkin'},
        'http': {'request': {'method': 'GET'}, 'response': {'status_code': 200}}}, True)
    # In-window decoys: same account on another host; encoded command on another host;
    # same endpoint to a different destination. No attack/benign labels in public docs.
    d = add('windows-security', '10', {'host': {'name': 'WS-02'},
        'user': {'name': 'lab-user'}, 'source': {'ip': '10.10.10.80'},
        'winlog': {'logon': {'type': 2}}})
    d['event'].update(code='4624', outcome='success')
    d = add('sysmon', '11', {'host': {'name': 'WS-02'}, 'user': {'name': 'admin'},
        'process': {'name': 'powershell.exe', 'command_line': 'powershell.exe -EncodedCommand ' + cmd}})
    d['event']['code'] = '1'
    add('zeek', '15', {'source': {'ip': '10.10.10.21'},
        'destination': {'ip': '10.10.10.60', 'port': 80}, 'url': {'original': 'http://10.10.10.60/index.html'}})
    for s in SOURCES:
        for t in ['2026-10-22T13:55:00+08:00', '2026-10-22T14:35:00+08:00']:
            d = add(s, '20', {'user': {'name': 'office-user'}, 'host': {'name': 'WS-03'}})
            d['@timestamp'] = t
            if s == 'windows-security':
                d['event']['code'] = '4624'
            elif s == 'sysmon':
                d['event']['code'] = '1'
                d['process'] = {'name': 'notepad.exe', 'command_line': 'notepad.exe notes.txt'}
            else:
                d.update(source={'ip': '10.10.10.30'}, destination={'ip': '10.10.10.60', 'port': 80})
    public.mkdir(parents=True, exist_ok=True)
    for s, docs in events.items():
        (public / (s + '.ndjson')).write_text(''.join(canonical(d) + '\n' for d in docs), encoding='utf-8')
    # Stable bulk actions preserve index-qualified IDs for the comparison and ground truth.
    lines = []
    for docs in events.values():
        for d in docs:
            lines.extend([canonical({'create': {'_index': d['_index'], '_id': d['_id']}}), canonical(d['_source'])])
    (public / 'bulk.ndjson').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    config = {'schema_version': 1, 'dataset_kind': 'synthetic_fixture',
        'hypothesis': 'Did lab-user on WS-01 show repeated failed logons, a successful remote logon, encoded PowerShell, and a subsequent outbound connection to the lab server?',
        'start': '2026-10-22T14:00:00+08:00', 'end': '2026-10-22T14:30:00+08:00',
        'required_sources': SOURCES, 'host_ip_map': {'WS-01': '10.10.10.21'},
        'index_aliases': SOURCES, 'counts': {s: len(d) for s, d in events.items()}}
    write(public / 'scenario.json', config)
    write(private / 'ground_truth.json', {'schema_version': 1, 'dataset_kind': 'synthetic_fixture',
        'expected_verdict': 'confirmed', 'relevant_evidence': relevant,
        'note': 'Confirmed means the staged indicator sequence exists, not proof of actual compromise. Zeek establishes host/time correlation only; it cannot attribute the connection to PowerShell.',
        'sequence': ['8 x 4625', '4624 logon type 3', 'Sysmon 1 encoded PowerShell', 'Zeek HTTP'],
        'decoys': [f"{d['_index']}:{d['_id']}" for docs in events.values() for d in docs if f"{d['_index']}:{d['_id']}" not in relevant]})
    return config

def freeze(data, config, assets, out):
    cfg = read(config)
    required = ['model', 'model_parameters', 'prompt_version', 'tool_version', 'schema_version', 'index_snapshot']
    if any(k not in cfg or cfg[k] in (None, '', 'TODO') for k in required):
        raise ValueError('freeze config requires concrete values: ' + ', '.join(required))
    root = Path(data)
    files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(root.rglob('*')) if p.is_file()}
    if not files:
        raise ValueError('dataset is empty')
    paths = [Path(p) for p in assets]
    if len({p.name for p in paths}) != len(paths):
        raise ValueError('freeze asset basenames must be unique')
    obj = {'dataset_files': files, 'configuration': cfg, 'scenario': read(root / 'scenario.json'),
           'assets': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    obj['freeze_id'] = digest(obj)
    write(out, obj)
    return obj

def requests(rec):
    q = rec.get('query', {})
    return q.get('requests', [q['request']] if 'request' in q else [])

def normalize(x):
    # Object key ordering only. Keep arrays, limits, time bounds and sort semantics intact.
    return canonical(x)

def overlap(a, b):
    return len(a & b) / len(a | b) if a | b else None

def evaluate(run, frozen):
    run = Path(run)
    r = read(run / 'report.json')
    if r.get('verdict') not in ['confirmed', 'rejected', 'inconclusive']:
        raise ValueError('invalid verdict')
    rows = [json.loads(x) for x in (run / 'ledger.jsonl').read_text().splitlines() if x.strip()]
    if not rows or any(x.get('run_id') != r.get('run_id') for x in rows):
        raise ValueError('empty ledger or mixed/mismatched run IDs')
    seqs = [x['seq'] for x in rows]
    if len(set(seqs)) != len(seqs):
        raise ValueError('duplicate ledger sequence')
    for x in rows:
        if x.get('query_hash') != digest(x['query']):
            raise ValueError('ledger query hash mismatch')
    allowed = set(frozen['scenario']['required_sources'])
    queries, evidence, queried, violations, fetched = set(), set(), set(), set(), set()
    for x in rows:
        for req in requests(x):
            idx = req.get('index')
            if idx is not None and idx not in allowed:
                violations.add(idx)
            if x['status'] != 'ok':
                continue
            if req.get('op') == 'search' and x['tool'] in ['search_events', 'aggregate_events', 'run_sequence_query']:
                queried.add(idx)
                queries.add(normalize(req))
        if x['status'] == 'ok' and x.get('doc_ids'):
            idxs = {q['index'] for q in requests(x) if 'index' in q}
            if len(idxs) != 1:
                raise ValueError('cannot attribute ledger doc IDs to one index')
            idx = next(iter(idxs))
            evidence.update(f'{idx}:{d}' for d in x['doc_ids'])
            if x['tool'] == 'fetch_evidence':
                fetched.update((x['seq'], idx, d) for d in x['doc_ids'])
    # Cite successful fetch_evidence calls, not just a model's claimed supported flag.
    claims = r.get('claims', [])
    if not isinstance(claims, list) or len({c['id'] for c in claims}) != len(claims):
        raise ValueError('claims must have unique IDs')
    covered = 0
    for c in claims:
        refs = c.get('citations', [])
        covered += bool(refs) and all((v['ledger_seq'], v['index'], v['doc_id']) in fetched for v in refs)
    cov = r.get('source_coverage', {})
    temporal = {}
    for s in allowed:
        c = cov.get(s, {})
        try:
            # Collector continuity is separate from min/max event timestamps.
            temporal[s] = c.get('collector_complete') is True and stamp(c['start']) <= stamp(frozen['scenario']['start']) and stamp(c['end']) >= stamp(frozen['scenario']['end'])
        except (KeyError, TypeError, ValueError):
            temporal[s] = False
    return {'run_id': r['run_id'], 'freeze_matches': r.get('freeze_id') == frozen['freeze_id'],
        'verdict': r['verdict'], 'source_coverage': len(queried & allowed) / len(allowed),
        'time_window_coverage_declared': temporal,
        'citation_reference_coverage': covered / len(claims) if claims else None,
        'citation_note': 'Checks retrievable reference linkage only. Human semantic support review and independent coverage records still required.',
        'allowlist_violations': sorted(violations), 'tool_calls': len(rows),
        'tool_errors': sum(x['status'] != 'ok' for x in rows),
        'ledger_truncated': any(x.get('doc_ids_truncated', False) for x in rows),
        'runtime_seconds': r.get('runtime_seconds'), 'model_usage': r.get('model_usage'),
        '_queries': queries, '_evidence': evidence,
        '_claims': {canonical({'id': c['id'], 'statement': c['statement']}) for c in claims}}

def compare(a, b, manifest, truth=None):
    f = read(manifest)
    check = dict(f)
    check.pop('freeze_id')
    if digest(check) != f['freeze_id']:
        raise ValueError('freeze manifest integrity failure')
    runs = [evaluate(a, f), evaluate(b, f)]
    if runs[0]['run_id'] == runs[1]['run_id']:
        raise ValueError('two independent run IDs required')
    result = {'schema_version': 1, 'freeze_id': f['freeze_id'],
        'conditions_match_declared': all(r['freeze_matches'] for r in runs),
        'verdict_agreement': runs[0]['verdict'] == runs[1]['verdict'],
        'query_jaccard': overlap(*(r['_queries'] for r in runs)),
        'evidence_jaccard': overlap(*(r['_evidence'] for r in runs)),
        'claim_exact_jaccard': overlap(*(r['_claims'] for r in runs)),
        'claim_note': 'Exact ID/statement agreement; paraphrases are differences, not semantic contradictions.',
        'differences': {k[1:]: {'only_a': sorted(runs[0][k] - runs[1][k]), 'only_b': sorted(runs[1][k] - runs[0][k])}
                        for k in ['_queries', '_evidence', '_claims']}}
    if truth:
        t = read(truth)
        relevant = set(t['relevant_evidence'])
        for r in runs:
            found = r['_evidence']
            r['ground_truth'] = {'verdict_correct': r['verdict'] == t['expected_verdict'],
                'retrieved_relevant_recall': len(found & relevant) / len(relevant) if relevant else None,
                'retrieved_relevant_precision': len(found & relevant) / len(found) if found else None}
    result['runs'] = [{k: v for k, v in r.items() if not k.startswith('_')} for r in runs]
    result['assessment_status'] = 'metrics_only_pending_human_review'
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('dataset'); s.add_argument('--public', required=True); s.add_argument('--private', required=True)
    s = sub.add_parser('freeze'); s.add_argument('--data', required=True); s.add_argument('--config', required=True); s.add_argument('--asset', action='append', required=True); s.add_argument('--out', required=True)
    s = sub.add_parser('compare'); s.add_argument('--a', required=True); s.add_argument('--b', required=True); s.add_argument('--manifest', required=True); s.add_argument('--truth'); s.add_argument('--out', required=True)
    a = p.parse_args()
    try:
        if a.cmd == 'dataset':
            print(json.dumps(dataset(a.public, a.private)['counts']))
        elif a.cmd == 'freeze':
            print(freeze(a.data, a.config, a.asset, a.out)['freeze_id'])
        else:
            result = compare(a.a, a.b, a.manifest, a.truth)
            write(a.out, result)
            print(json.dumps({k: v for k, v in result.items() if k not in ['runs', 'differences']}))
    except (ValueError, KeyError, TypeError, OSError) as e:
        p.exit(2, f'error: {e}\n')

if __name__ == '__main__':
    main()
