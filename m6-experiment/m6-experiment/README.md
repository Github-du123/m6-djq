# M6: Experiment and Product

Python 3.10+, standard library only. Run commands from the project root.
This module adds files only under `m6-experiment`; M1-M4 are unchanged.

## Current scope and honest status

Implemented: reproducible synthetic ECS fixtures, hard decoys, separate private ground truth,
configuration/dataset/asset hashing, M4 ledger reader, two-run metrics and difference log,
and unit/contract tests. No real ELK ingestion, agent run, model cost or measured repeatability
result has been claimed. M3 and M5 implementation are absent in the supplied archive.

Synthetic fixtures bypass M2/M3 and do NOT demonstrate pull/push/stream or parser fallback.
Live event generation is a separate team lab task described in RUNBOOK.md.

## 1. Generate data

Choose an M6-only private folder OUTSIDE the repository and the agent workspace:

```bash
python m6-experiment/experiment.py dataset --public lab/m6-public --private ../m6-private
```

Produces 20 events: Windows 12, Sysmon 4, Zeek 4. Includes eight failed logons,
one successful network logon, one harmless encoded process command, one synthetic HTTP
connection, three in-window decoys and six boundary events. Scenario time is
22 October 2026, 14:00-14:30 Singapore (+08:00), end exclusive.
`host_ip_map` links WS-01 to 10.10.10.21. The remote logon origin 10.10.10.99
is a different entity. Zeek has no invented username or process attribution.

`bulk.ndjson` uses Elasticsearch `create` actions and fixed IDs. Preserve IDs across runs.
It matches the fields allowed by M1's strict index template. Use only an isolated lab
with the M1 templates and the three exact configured index names. Review existing lab
indices first; do not overwrite shared datasets. Submit the bulk file through the team's
approved authenticated ingestion procedure, check **every** bulk item (HTTP 200 alone
is insufficient), refresh, and verify counts 12/4/4. A second import deliberately returns
ID conflicts; it is not a second clean experiment. Never run M4's destructive dev seeder
against the shared stack. No indexing credentials are included here.

The manifest is PRIVATE. Do not commit it, pass it to M5 or an LLM, or put its path
in the prompt. Deterministic synthetic data is for engineering repeatability, not a blind
benchmark. For an independent blind assessment, M6 must create a new unseen lab dataset.

## 2. Freeze

Create a concrete `freeze-config.json` recording:

```json
{
  "model": "actual-model-and-revision",
  "model_parameters": {"temperature": 0, "seed": 42},
  "prompt_version": "actual-prompt-revision",
  "tool_version": "actual-M4-commit",
  "schema_version": "actual-approved-M3-revision-or-explicit-fixture-bypass",
  "index_snapshot": "actual-snapshot-or-export-digest"
}
```

Use the provider's actual supported parameters; temperature/seed do not guarantee identical
outputs. Do not use the illustrative values above as experiment evidence.

```bash
python m6-experiment/experiment.py freeze --data lab/m6-public --config freeze-config.json --asset actual-prompt.txt --asset m4-mcp/tracehunt_mcp/tools.py --out evidence/m6-freeze.json
```

Repeat `--asset` for all relevant prompts, tool/config/schema source files or a deterministic
source archive. Config bytes are parsed and canonicalized; datasets/assets are byte-hashed.
Keep output OUTSIDE the dataset directory. Before EACH run re-run this command to a
separate manifest and compare `freeze_id` with the frozen one. Also independently verify
the actual ES export/snapshot and model settings. A matching report freeze ID alone is only
a declaration; it cannot prove the index remained unchanged. Stop if conditions drift.

## 3. M5 export contract (new proposed interface, not existing M5 behavior)

Each clean run directory must contain unmodified M4 `ledger.jsonl`, `report.json`, original
report text, plan, raw tool responses, prompt/config snapshot and coverage records.
Set M4 `TRACEHUNT_RUN_ID` and `TRACEHUNT_LEDGER_PATH` to a new ID/path for each run.
Do not append a second run to the first ledger. Keep both runs' documents and indices fixed.

`report.json` shape:

```json
{
  "run_id": "run-a",
  "freeze_id": "copy-the-verified-freeze-id",
  "verdict": "inconclusive",
  "runtime_seconds": 12.4,
  "model_usage": {"input_tokens": 1000, "output_tokens": 500},
  "source_coverage": {
    "windows-security": {"start": "2026-10-22T14:00:00+08:00", "end": "2026-10-22T14:30:00+08:00", "collector_complete": true},
    "sysmon": {"start": "2026-10-22T14:00:00+08:00", "end": "2026-10-22T14:30:00+08:00", "collector_complete": true},
    "zeek": {"start": "2026-10-22T14:00:00+08:00", "end": "2026-10-22T14:30:00+08:00", "collector_complete": true}
  },
  "claims": [
    {"id": "stable-claim-id", "statement": "A factual statement.",
     "citations": [{"index": "windows-security", "doc_id": "actual-id", "ledger_seq": 12}]}
  ]
}
```

The example is a FORMAT ONLY, not a completed report. Every factual statement in the
human-readable report must appear in claims. Citations must point to a successful M4
`fetch_evidence` entry and that entry's returned ID. Keep missing model usage/runtime null,
not zero. `collector_complete` needs independent collector/fixture generation evidence;
min/max event timestamps cannot establish collection continuity.

## 4. Compare after both reports are final

```bash
python m6-experiment/experiment.py compare --a evidence/run-a --b evidence/run-b --manifest evidence/m6-freeze.json --truth ../m6-private/ground_truth.json --out evidence/m6-comparison.json
python -m unittest discover -s m6-experiment/tests -v
```

JSON contains per-run metrics, two-run overlap and exact difference lists. `--truth` is
optional and used ONLY by M6 after frozen runs. Ground truth remains outside agent access.

| Measure | Definition / limitation |
|---|---|
| Query overlap | Jaccard of successful hunt search/aggregation/sequence request sets; excludes discovery/history/fetch; retains index, limits, sorting, bounds and array order |
| Evidence overlap | Jaccard of successful ledger `(index, document ID)` pairs; different indices cannot collide |
| Verdict agreement | Same confirmed/rejected/inconclusive; agreement does not establish correctness |
| Claim overlap | Exact stable ID and statement match; wording changes are visible, semantic agreement needs review |
| Source coverage | Required sources queried by successful hunt searches / required sources; discovery alone does not count |
| Time coverage | Declared collector continuity and enclosing interval per source; independent verification required |
| Citation reference coverage | Claims with nonempty references all linked to successful fetches / listed claims; NOT proof of semantic support |
| Ground-truth verdict | Verdict equals hidden expected verdict |
| Retrieval relevance | Relevant evidence retrieved / expected relevant evidence (recall); relevant / all retrieved (precision) |
| Cost | Tool count/errors, observed runtime and model usage if exported; tool durations are not total runtime |

Empty/empty Jaccard is null, never perfect reproducibility. M4 truncates ledger IDs at 100;
`ledger_truncated` flags this and evidence overlap/recall may then be incomplete. Retrieve
smaller batches and retain full raw responses. Broad discovery can legitimately retrieve
decoys: retrieval precision is not claim precision. Queries are normalized only by JSON key
ordering, conservatively avoiding false claims that different queries are equivalent.
Bad hashes, duplicate sequences, mixed runs, invalid verdicts and altered freeze manifests
fail with exit code 2. Comparison output is metrics, never an automatic assessment pass.

## Team handoff

- M1: provision isolated indices, verify ECS template/bulk results, freeze exports, review rebuild steps.
- M2: provide real collector continuity/status and live pull/push/stream evidence.
- M3: provide approved schema version and run actual connector output through validation.
- M4: retain current ledger contract; fetch every cited document; no interface change needed.
- M5: agree the proposed report export above; preserve all factual claims and full tool responses.
- M6: keep truth private, execute freeze/run A/run B/evaluate sequence, interpret differences,
  lead experiment tables, limitations, conclusion, demo comparison and pitch.
