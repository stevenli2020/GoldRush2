# Tranche 3 Step 4 Phase B Report

**Execution date:** 2026-09-07  
**Frozen scope:** 18 variables listed below only  
**Phase C:** not executed

## Commands

Each command was run separately in WSL with `--force -v`:

```text
gr2 extract L0-002 --force -v
gr2 extract L0-003 --force -v
gr2 extract L0-005 --force -v
gr2 extract L0-006 --force -v
gr2 extract L1-005 --force -v
gr2 extract L3-005 --force -v
gr2 extract L4-001 --force -v
gr2 extract L4-002 --force -v
gr2 extract L4-006 --force -v
gr2 extract L4-007 --force -v
gr2 extract L4-009 --force -v
gr2 extract L5-001 --force -v
gr2 extract L5-002 --force -v
gr2 extract L5-003 --force -v
gr2 extract L5-006 --force -v
gr2 extract L7-003 --force -v
gr2 extract L8-001 --force -v
gr2 extract L9-004 --force -v
```

All 18 commands completed successfully. No `gr2 analyze` or `gr2 analyze-strategies` command was run.

## Long-horizon status check

Several legacy extractors do not emit a `status` field; those are reported as `NOT_EMITTED`, not inferred as `VALID`.

| Variable | 1-3y before → after | 3-10y before → after | Result |
|---|---|---|---|
| L0-002 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L0-003 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L0-005 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L0-006 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L1-005 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L3-005 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L4-001 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L4-002 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L4-006 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L4-007 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L4-009 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L5-001 | VALID → VALID | INSUFFICIENT_DATA → VALID | 3–10y history now sufficient |
| L5-002 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L5-003 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L5-006 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L7-003 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |
| L8-001 | VALID → VALID | INSUFFICIENT_DATA → VALID | 3–10y history now sufficient |
| L9-004 | NOT_EMITTED → NOT_EMITTED | NOT_EMITTED → NOT_EMITTED | no status contract |

The two observable degraded-to-valid lifts are L5-001 and L8-001. The remaining files cannot be classified as `DEGRADED`/`VALID` from their current JSON because their extractors predate the status-field contract. No status uplift is claimed for them.

## Expected degradation

No target output reported a post-refresh `DEGRADED` or `INSUFFICIENT_DATA` status in the two requested horizons. The prior `INSUFFICIENT_DATA` states for L5-001 and L8-001 were cleared because the refreshed sources supplied at least 120 monthly observations. Variables without status fields require a separate schema-contract task before their degradation semantics can be audited.

## Anti-leakage verification

Before extraction, 27 non-target current JSON files were recorded with SHA-256 and `st_mtime_ns`. After all 18 commands:

| Protected files | Hash changes | mtime changes | Result |
|---:|---:|---:|---|
| 27 | 0 | 0 | PASS |

No out-of-scope current JSON file was changed or touched.
