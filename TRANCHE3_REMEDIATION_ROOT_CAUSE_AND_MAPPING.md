# Tranche 3 Remediation — Root Cause and Window Mapping

## Root cause

L4-006 was missed because the initial audit focused on shared WGC helpers and the approved Tranche 3 inventory, while this extractor retained a private `HORIZON_LOOKBACKS = {1-3y: 8, 3-10y: 20}` dictionary. No repository-wide consistency check inspected private constants.

## Implemented mapping

| Frequency | Implemented rule |
|---|---|
| Daily | Explicit 5-day/20-day rolling comparisons; no 252/756 row-count horizon. |
| Weekly | Source-specific weekly lookbacks; no monthly/quarterly rule is applied. |
| Monthly ordinary | 36 observations for 1-3y; 120 for 3-10y. |
| Monthly derived 12m | 48 including warmup; 132 including warmup. |
| Quarterly | 12 complete quarters for 1-3y; 40 for 3-10y. |
| Annual/event-driven | Source-specific applicability; no monthly/quarterly row-count substitution. |

The registry and consistency checker are deliverables of this remediation. L4-006 is frozen as `NOT_APPLICABLE` with zero confidence pending approval.

## Validation status

The window consistency checker and Python syntax validation pass. The full WSL suite with the two quarantined network tests excluded currently reports **827 passed, 11 failed, 2 deselected**. All 11 failures are legacy L4-006 tests asserting the pre-freeze directional behavior and old 8/20 lookbacks; they are intentionally incompatible with the new zero-confidence gate and require test-contract updates before a zero-failure claim can be made.
