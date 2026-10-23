# M6 — Experiment and Product


M6 generates controlled log fixtures, processes them through M3, preserves a separate ground-truth manifest, exercises M4 search tools, and compares two investigation runs.

## Requirements

- Python 3.11 or later.
- The supplied M1–M4 directories.
- No additional Python packages for offline checks.
- The existing M4 Elasticsearch dependencies and a running ELK environment for live checks.


Run all commands below from the project root.

## Features

- Synthetic Windows Security, Sysmon, and Zeek records following M2 adapter output structures.
- Actual M3 normalization, schema registration, parser reuse, and quarantine checks.
- Ground truth using the document IDs returned by M3.
- Dataset, source-code, configuration, and prompt-asset hashing.
- Integration checks using the actual M4 `ToolSet` and `EvidenceLedger`.
- Two-run comparison with JSON, CSV, Markdown, and HTML outputs.
- Generated experiment summaries and Kibana saved-object configurations.
- Read-only verification of a small, isolated Elasticsearch dataset.

## Module Structure

| File | Purpose |
|---|---|
| `experiment.py` | Command-line entry point |
| `tracehunt_experiment/dataset.py` | Dataset generation and M3 integration |
| `tracehunt_experiment/freeze.py` | Experiment freezing and verification |
| `tracehunt_experiment/run.py` | M4 tool integration checks |
| `tracehunt_experiment/backend.py` | Strict offline fixture backend |
| `tracehunt_experiment/snapshot.py` | Read-only Elasticsearch verification |
| `tracehunt_experiment/compare.py` | Run comparison and table exports |
| `tracehunt_experiment/product.py` | Kibana configuration and report summaries |
| `fixtures/` | Generated data and schema-validation artifacts |
| `examples/` | Executed offline runs and comparison outputs |
| `tests/` | M6 tests |
| `M5_CONTRACT.md` | Proposed M5-to-M6 export interface |
| `VALIDATION.md` | Completed checks and remaining validation |

## Quick Start

Check the included dataset and run the tests:

```bash
python m6-experiment/experiment.py check-data --dataset m6-experiment/fixtures
python -m unittest discover -s m6-experiment/tests -v
```

The included dataset contains 20 events:

| Source | Total Events | Events Inside the Hunt Window |
|---|---:|---:|
| Windows Security | 12 | 10 |
| Sysmon | 4 | 2 |
| Zeek | 4 | 2 |
| **Total** | **20** | **14** |

The hunt window is **23 October 2026, 14:00–14:30 Singapore time (+08:00)**. The ending timestamp is excluded.

The target sequence contains repeated failed logons, a successful network logon, a harmless encoded PowerShell process, and a subsequent host-correlated HTTP connection. Decoys include activity from another host, another destination, and events outside the window.

These are synthetic records. The generator does not execute commands, perform logons, or send network requests.

## Generate a New Dataset

```bash
python m6-experiment/experiment.py prepare --out lab/m6-v2-data --private ../m6-private-v2
```

Both output directories must be empty and must not contain one another.

The public output includes raw records, M3-normalized events, a bulk-import payload, schema decisions, quarantine records, an approved custom parser, and a dataset manifest.

The private output contains the expected verdict and event-level ground truth.

**Keep the private directory outside the repository and the hunt agent’s workspace. Do not provide it to M5 or the model during an investigation.**

Two additional unknown-format samples and two malformed records test schema generation, parser reuse, and quarantine. They remain separate from the main hunt dataset.

## Freeze the Offline Experiment

```bash
python m6-experiment/experiment.py freeze --dataset m6-experiment/fixtures --config m6-experiment/smoke-config.json --asset m6-experiment/SMOKE_PROTOCOL.md --out evidence/m6-smoke-freeze.json
```

Verify the frozen conditions before running:

```bash
python m6-experiment/experiment.py verify-freeze --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --config m6-experiment/smoke-config.json --asset m6-experiment/SMOKE_PROTOCOL.md
```

Changing the dataset, relevant source files, configuration, or supplied assets requires a new freeze.

## Run Two Offline Integration Checks

```bash
python m6-experiment/experiment.py smoke --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --run-id smoke-a --out evidence/m6-smoke-a

python m6-experiment/experiment.py smoke --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --run-id smoke-b --out evidence/m6-smoke-b
```

Use different run IDs and empty output directories.

These commands call the actual M4 Python tools against a local fixture backend. They exercise query construction, input validation, evidence retrieval, aggregation, sequence queries, and ledger recording.

They do not run Elasticsearch, the MCP stdio transport, M5, or an LLM. The smoke verdict remains `inconclusive` because M5 hypothesis verification has not run.

## Compare the Runs

```bash
python m6-experiment/experiment.py compare --run-a evidence/m6-smoke-a --run-b evidence/m6-smoke-b --manifest evidence/m6-smoke-freeze.json --out evidence/m6-smoke-comparison
```

Outputs include:

- `comparison.json`
- `comparison.csv`
- `comparison.md`
- `comparison.html`
- `differences.json`
- `REPORT_SUMMARY.md`

After both final investigation reports are complete, M6 can add private ground-truth scoring:

```bash
python m6-experiment/experiment.py compare --run-a evidence/agent-a --run-b evidence/agent-b --manifest evidence/agent-freeze.json --truth ../m6-private-v2/ground_truth.json --out evidence/m6-final-comparison
```

The manifest must belong to the same dataset.

## Evaluation Measures

| Measure | Meaning |
|---|---|
| Query Jaccard | Overlap between successful hunt-query sets |
| Evidence Jaccard | Overlap between index-qualified document-ID sets |
| Verdict agreement | Whether both runs return the same verdict |
| Exact claim Jaccard | Agreement between stable claim IDs and statement text |
| Source coverage | Proportion of required sources queried |
| Query-window coverage | Whether query intervals cover the requested window |
| Declared time coverage | Whether the exported coverage declarations enclose the window |
| Citation linkage | Claims linked to successful evidence-fetch ledger entries |
| Archived citation coverage | Claims whose references also appear in archived fetch responses |
| Plan completion | Proportion of exported plan items marked complete |
| Operational cost | Tool counts, errors, recorded runtime, and available token usage |

Empty comparisons and unavailable measurements remain `null`.

Citation linkage does not prove that an event supports a statement. Human review must check factual support, report completeness, and collection continuity.

## Elasticsearch Verification

M1 should import `normalized/bulk.ndjson` into an isolated environment through the approved ingestion procedure and check every bulk response item. The payload uses `create` actions with M3-generated IDs.

M6 does not delete, recreate, or write to shared indices.

Configure the existing M4 connection variables, then run:

```bash
python m6-experiment/experiment.py verify-index --dataset m6-experiment/fixtures --out evidence/m6-index-check.json
```

For a live typed-tool check:

```bash
python m6-experiment/experiment.py smoke --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --run-id es-smoke-a --backend elasticsearch --out evidence/m6-es-smoke-a
```

Live smoke checks verify index contents before and after execution. The export check supports small isolated datasets, with a maximum complete read of 10,000 documents per index.

## Kibana Configuration

```bash
python m6-experiment/experiment.py kibana --dataset m6-experiment/fixtures --out evidence/m6-kibana
```

The output contains one data view, four saved searches, a dashboard, and import instructions.

The configuration has passed local JSON and reference checks. Import compatibility and rendering still require validation in the team’s Kibana environment.

## M5 Integration

Follow `M5_CONTRACT.md` when exporting actual agent runs.

Each run must retain its structured report, unmodified M4 ledger, complete tool responses, plan, and coverage records. Use clean sessions and keep the first run’s report outside the second run’s context.

Fill in `agent-config.example.json` with the actual experiment settings before freezing. Do not use the offline smoke configuration for an agent experiment.

## Validation Status

- **23 M6 tests passed.**
- **130 supplied M3 tests passed.**
- **97 original M1–M4 files verified unchanged.**
- Two offline M4 integration runs completed with **15 tool calls each and no tool errors**.

These checks establish offline integration behavior. Real collector execution, live ELK/Kibana validation, MCP transport checks, and two independent M5/LLM investigations remain outstanding.