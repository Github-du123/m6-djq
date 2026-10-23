# M6 — Experiment and Evaluation

This folder contains the M6 experiment tools for TraceHunt.

**Start with the offline workflow below.** It verifies integration with the existing M3 parser and M4 tools without requiring Elasticsearch or an LLM.

## 1. Add This Folder to the Project

Extract `SE6014_M6_Code_v2.zip` and copy its `m6-experiment` folder into the existing project root.

The project root must contain these folders:

- `m1-elk`
- `m2-connectors`
- `m3-schema`
- `m4-mcp`
- `m5-hunt`
- `m6-experiment`

Do not place `m6-experiment` inside another member’s folder.

If an older M6 folder exists, back up its experiment records and replace the old code with this version. **Do not mix v1 and v2 scripts or run files.**

The supplied M1–M4 code does not need modification.

## 2. Requirements

- Python **3.11 or later**
- The supplied M1–M4 source folders

Check Python:

```bash
python --version
```

The offline workflow uses Python’s standard library and imports M3/M4 directly from the sibling folders. No additional package installation is required.

**Run every command below from the project root**, where all six member folders are located.

## 3. Check the Included Dataset and Tests

The package already includes generated data in `m6-experiment/fixtures`. You do not need to generate it again for the first run.

```bash
python m6-experiment/experiment.py check-data --dataset m6-experiment/fixtures
```

Success: the command prints a `dataset_id` and exits without an error.

Run the tests:

```bash
python -m unittest discover -s m6-experiment/tests -v
```

Expected result:

```text
Ran 23 tests
OK
```

These tests call the existing M3 parser and M4 tools, including schema fallback, quarantine, evidence retrieval, and comparison checks.

## 4. Run the Offline Integration Workflow

Run the following commands in order.

### Step A — Freeze the setup

```bash
python m6-experiment/experiment.py freeze --dataset m6-experiment/fixtures --config m6-experiment/smoke-config.json --asset m6-experiment/SMOKE_PROTOCOL.md --out evidence/m6-smoke-freeze.json
```

Success: the command prints `dataset_id` and `freeze_id`.

### Step B — Verify the frozen setup

```bash
python m6-experiment/experiment.py verify-freeze --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --config m6-experiment/smoke-config.json --asset m6-experiment/SMOKE_PROTOCOL.md
```

This checks that the dataset, relevant source files, configuration, and supplied protocol still match the freeze.

### Step C — Run the first tool check

```bash
python m6-experiment/experiment.py smoke --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --run-id smoke-a --out evidence/m6-smoke-a
```

### Step D — Run the second tool check

```bash
python m6-experiment/experiment.py smoke --dataset m6-experiment/fixtures --manifest evidence/m6-smoke-freeze.json --run-id smoke-b --out evidence/m6-smoke-b
```

### Step E — Compare both runs

```bash
python m6-experiment/experiment.py compare --run-a evidence/m6-smoke-a --run-b evidence/m6-smoke-b --manifest evidence/m6-smoke-freeze.json --out evidence/m6-smoke-comparison
```

### Step F — Open the results

Open this file in a browser:

```text
evidence/m6-smoke-comparison/comparison.html
```

The same directory also contains:

| File | Purpose |
|---|---|
| `comparison.json` | Complete comparison metrics |
| `comparison.csv` | Table for Excel or report editing |
| `comparison.md` | Readable Markdown table |
| `differences.json` | Exact query, evidence, and claim differences |
| `REPORT_SUMMARY.md` | Generated English experiment summary |

For this deterministic offline workflow, expected query, evidence, and exact-claim Jaccard values are **1.0**.

Each run should contain **15 tool calls with no tool errors**.

**Important:** these are M4 tool integration checks against an offline fixture backend. No M5 agent or LLM runs. The verdict is intentionally `inconclusive`.

## 5. Understand the Run Files

Each run directory contains:

| File | Contents |
|---|---|
| `run.json` | Structured report and run metadata |
| `ledger.jsonl` | Actual M4 evidence-ledger records |
| `responses.jsonl` | Actual M4 tool arguments and returned results |
| `backend_responses.jsonl` | Responses from the selected backend |

Use the ledger and response files when investigating a comparison result.

## 6. Dataset and Ground Truth

The included dataset contains:

- 12 Windows Security events
- 4 Sysmon events
- 4 Zeek events

The scenario window is **23 October 2026, 14:00–14:30 Singapore time (+08:00)**, excluding the ending timestamp.

M6 creates synthetic raw records following M2 adapter structures, then processes them through the actual M3 parser. Normalized fields and document IDs come from M3.

To generate another copy:

```bash
python m6-experiment/experiment.py prepare --out lab/m6-v2-data --private ../m6-private-v2
```

Both output directories must be empty.

The separate private package contains `ground_truth.json`. It is only needed for evaluator scoring after both investigation reports are complete.

**Do not commit the private manifest or provide it to the hunt agent.** The initial offline workflow does not require it.

## 7. Connect to M5

The supplied M5 folder is currently empty. M6 does not implement the hunt agent.

The M5 developer should read **`m6-experiment/M5_CONTRACT.md`** and export each investigation using that interface.

The minimum integration requirements are:

1. Use a unique run ID and ledger path for each investigation.
2. Save the structured report as `run.json`.
3. Preserve the original M4 `ledger.jsonl`.
4. Save full tool results in `responses.jsonl`.
5. Include claims, citations, plan statuses, coverage declarations, runtime, and available model usage.
6. Copy the correct `dataset_id` and `freeze_id` into each report.

This version expects **v2 `run.json` exports**, not the earlier v1 `report.json` format.

For real agent experiments, fill in `agent-config.example.json` with actual settings, freeze the actual prompt, and run two independent sessions.

After both runs finish:

```bash
python m6-experiment/experiment.py compare --run-a evidence/agent-a --run-b evidence/agent-b --manifest evidence/agent-freeze.json --truth ../m6-private-v2/ground_truth.json --out evidence/m6-final-comparison
```

Use the private manifest corresponding to the evaluated dataset.

## 8. Connect to Elasticsearch and Kibana

For live checks, first follow M1/M4 setup instructions and configure the existing M4 connection environment variables.

M1 should import:

```text
m6-experiment/fixtures/normalized/bulk.ndjson
```

The bulk payload uses `create` actions with M3-generated IDs. Check every bulk response item. M6 does not delete or recreate shared indices.

Verify the imported documents:

```bash
python m6-experiment/experiment.py verify-index --dataset m6-experiment/fixtures --out evidence/m6-index-check.json
```

Generate Kibana import files:

```bash
python m6-experiment/experiment.py kibana --dataset m6-experiment/fixtures --out evidence/m6-kibana
```

Follow the generated `IMPORT.md`. Actual Kibana import and rendering still require validation.

## 9. Common Problems

| Problem | What to check |
|---|---|
| Python version error | Use Python 3.11 or later |
| Missing M3/M4 folder | Place M6 beside the supplied M3/M4 folders |
| Output already exists | Use a new output filename or empty directory; preserve previous evidence |
| Freeze verification fails | Check which code, data, configuration, or asset changed, then create a new freeze |
| Dataset verification fails | Restore the original fixtures or regenerate them into a new directory |
| Ground-truth mismatch | Use the manifest generated for the same dataset |
| Missing citations or archived documents | Check M5 exports against `M5_CONTRACT.md` |
| Elasticsearch connection/import failure | Check M1/M4 configuration and bulk response items |

## 10. Current Validation Status

- 23 M6 tests passed.
- 130 supplied M3 tests passed.
- 97 original M1–M4 files remained unchanged.
- Two offline M4 integration runs completed successfully.

Live Elasticsearch/Kibana validation and two independent M5/LLM investigations remain to be completed in the team environment.
