# V3 validation record

Executed locally on Python 3.12.14 / Linux:

- M6: **41 tests passed**, including 18 review regressions.
- Unmodified M3: **130 tests passed**.
- M1–M4 originals: **97 archive files byte-identical**.
- M5 remains unimplemented and unchanged.
- Actual M3: 20 accepted hunt records, unknown-format parser creation/reload/reuse,
  two separately quarantined bad records.
- Actual M4 ToolSet / fixture backend: two runs, 15 calls each, zero errors and overlaps 1.0.
- Real-M4 ordered sequence regression: forward one match, reverse zero, query overlap 0.
- Real-M3/M4 101-document fetch regression: capped ledger 100, archived response 101,
  successful evaluation, citation linkage 100/101 and archive coverage 1.
- Copied Logstash/role changes and M5 additions/changes invalidate freezes.
- Effective limit drift invalidates freeze/smoke; intentionally newly frozen low limits
  propagate incompleteness into both run and comparison summaries.
- Keyword exact positives and partial/case negatives pass. Unsupported phrase matching
  on wildcard/text or unindexed fields raises rather than emulating substring behavior.

A new workflow explicitly runs M6 and M3 on the configured four OS/Python combinations.
Only local Linux/Python 3.12 tests ran here. Hosted jobs require maintainer authorization
and have not been executed in this delivery.

No live service privileges were changed. No live ELK, Kibana, MCP transport or model was
used. Checks validate supplied local code and fixtures, not real collector continuity,
agent repeatability or deployment state. See REVIEW_FIXES_V3.md for the review mapping.
