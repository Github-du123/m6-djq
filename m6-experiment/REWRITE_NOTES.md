# What changed from the earlier M6 version

1. Raw data now follows the M2 adapter shapes and runs through the actual M3 API.
2. Stable IDs, ECS fields, schema hashes and source hashes come from M3, not M6 guesses.
3. Unknown-format onboarding now creates and reloads a real registered M3 parser.
4. Bad known/custom records actually pass through M3's quarantine path.
5. Smoke runs call actual M4 ToolSet methods and EvidenceLedger, with raw responses retained.
6. Freeze verification checks the public dataset inventory plus current M1–M4/M6 source bytes.
7. Comparison links citations to fetch ledger entries AND archived response document IDs.
8. Query-window coverage, declared source coverage, truncation, missing responses and plan
   completion are separate metrics. CSV, Markdown, HTML and report summaries are generated.
9. Live read-only verification compares the complete small index exports with M3 results.
10. M5 run export uses version 2 (`run.json`). The old v1 `report.json` examples are incompatible.

Replace the old M6 CODE directory with this version. Keep historical experiment records,
private manifests and presentation files separately. Re-freeze after any code/data/prompt
change. Do not mix the old manifest IDs with this dataset or reuse old comparison files.

This code package does not replace the final group report or pitch deck. Use measured
agent results to update those materials after M5 integration.
