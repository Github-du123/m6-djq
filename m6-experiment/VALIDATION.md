# Validation record, 23 October 2026

## Executed checks

- M6: `python -m unittest discover -s m6-experiment/tests -v` — **23 passed**.
- Supplied M3: `python -m unittest discover -s m3-schema/tests -v` — **130 passed**.
- Original M1–M4: **97 archive files byte-compared, unchanged**.
- Hunt fixtures: **20 accepted by actual M3, 0 quarantined**; Windows 12, Sysmon 4, Zeek 4.
- Additional unknown-format samples: **2 accepted, 1 parser created**.
- Parser reload/frozen reuse: **2 accepted, 0 new parsers**.
- Separate malformed fixtures: **2 quarantined, 0 accepted**.
- Two sequential actual-M4 ToolSet runs against the strict fixture backend:
  **15 tool calls each, 0 tool errors**, source/query-window coverage 3/3.
- Citation linkage and archived citation reference coverage: **1.0** in both smoke runs.
- Query, evidence and exact-claim overlaps: **1.0** for this deterministic smoke protocol.
- Kibana artifact: 6 JSON saved objects with locally resolved references.

These are offline engineering checks. The smoke verdict is inconclusive because the
M5 verifier did not run. Tool overlap does not establish agent repeatability.

## Not executed

Docker/Elasticsearch/Kibana services were unavailable in this execution environment.
PowerShell M2 connector execution and real Windows/Zeek collection were not executed.
M4's independent pytest suite, live ES integration and MCP stdio smoke were not executed
here. The tests above directly exercised the real M4 Python tools and ledger instead.
No model was invoked. No real collector-continuity claim, screenshot or final pitch claim
has been added. Live Kibana imports require team verification.

## Audit location

`examples/run-a/` and `examples/run-b/` contain actual tool-run records, responses and
backend responses. `examples/comparison/` contains metrics and exact differences.
`examples/freeze.json` binds local source/data bytes to the smoke configuration.
The private event manifest is deliberately absent from this public package.
