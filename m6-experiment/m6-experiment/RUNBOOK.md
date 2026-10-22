
### Executive summary
TraceHunt investigates a threat-hunting hypothesis through typed, read-only MCP tools
on the Elastic Stack. Our evaluation design separates investigation inputs from a
private event manifest and compares two clean runs under frozen conditions. The
experiment assesses query selection, retrieved evidence, verdicts, factual claims and
citation traceability. At this stage, the M6 evaluation toolkit has passed offline tests;
end-to-end agent repeatability has not yet been measured.

### Experimental method
We prepared a controlled sequence containing repeated failed logons, a successful
network logon, an encoded PowerShell process and a subsequent host-correlated HTTP
connection. Benign events from other accounts, hosts and destinations were included
to test whether the investigation incorrectly linked unrelated activity. The current
fixtures are synthetic ECS documents and do not demonstrate live collection. Before
the final evaluation, the dataset, hypothesis, time interval, model settings, prompts,
schema and tool versions will be frozen. The hunt agent will run twice in separate
sessions without access to the evaluation manifest or the other run's output.

### Results table

| Measure | Run A | Run B | Comparison |
|---|---|---|---|
| Verdict | Not measured | Not measured | Not measured |
| Required sources queried | Not measured | Not measured | Target: 3/3 each |
| Verified collection interval | Not verified | Not verified | Target: all sources |
| Query overlap | — | — | Not measured |
| Evidence overlap | — | — | Not measured |
| Claim exact agreement | — | — | Not measured |
| Reference linkage coverage | Not measured | Not measured | Semantic review separate |
| Ground-truth verdict correctness | Not measured | Not measured | Evaluate privately |
| Runtime, tool calls, tokens | Not measured | Not measured | Not measured |

### Limitations
A single staged hypothesis cannot establish general detection accuracy. Synthetic
fixtures cannot validate real connector behavior or collection continuity. Event
bounds do not prove uninterrupted monitoring. Reference linkage does not establish
that a citation supports the associated claim. The current network evidence permits
host and time correlation, but not process-level attribution. Evidence-ledger
truncation may reduce measured overlap. A declared freeze ID must be checked against
independent dataset and configuration records. Matching verdicts can still be wrong.

### Conclusion before final runs
The M6 module provides a reproducible data preparation and evaluation procedure.
Offline tests verify key failure cases and compatibility with the supplied M1 mapping.
A final claim about agent repeatability requires two completed frozen runs, independent
coverage checks and a manual audit of factual support.
