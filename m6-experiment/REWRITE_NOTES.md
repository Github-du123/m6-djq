# V3 migration notes

V3 fixes the correctness defects documented in REVIEW_FIXES_V3.md. Package version is
3.0.0. Frozen/run/comparison schemas are 3. The deterministic dataset schema and content
remain unchanged; its separate private manifest remains valid only for its dataset_id.

Replace the entire old M6 directory; copy the new M6 CI workflow as well. Retain old
experiment evidence separately. Never relabel a v2 freeze/run as v3. Re-freeze and rerun
against the actual integration checkout and effective M4 limits.

Known behavior change: offline phrase matches on M1 keyword fields are complete,
case-sensitive equality. Unsupported phrase analyzers/wildcard fields fail explicitly.
Smoke selects the exact PowerShell process name and archives its command line for review.

M1–M5 source code, live privileges and remote branches are not changed by this archive.
