# Tranche 3 Step 1 — Long-Horizon Evidence Window Calibration

**Status:** approved; Step 3 implemented
**Scope:** monthly and quarterly variables currently feeding the 4-horizon strategy matrix

## Finding

Several monthly extractors reuse the daily lookback constants `5/63/252/756` as row counts. For monthly data this means 21 years for `1-3y` and 63 years for `3-10y`, even though the horizon names describe calendar horizons. This is the direct cause of widespread long-horizon `DEGRADED` statuses for modern series such as ETF flows.

The correct contract must distinguish:

- `comparison_horizon`: calendar duration represented by the signal;
- `minimum_evidence_observations`: minimum complete observations needed to validate the comparison;
- `warmup_observations`: extra observations required by a derived statistic such as a 12-month moving average;
- `calendar_completeness`: missing months/quarters are not silently compressed.

## Current inventory

| Frequency | Variables identified | Current pattern | Problem |
|---|---|---|---|
| Monthly | L0-002, L0-003, L1-005, L4-001, L4-002, L4-009, L5-001, L5-002, L5-006, L8-001 | Shared or local `5/63/252/756` row counts in several modules | Row counts are not month-based horizons; 756 monthly rows is structurally excessive |
| Quarterly | L0-005, L0-006, L3-005, L4-006, L4-007, L5-003, L7-003, L9-004 | Global default 12Q for 1-3y and 40Q for 3-10y, with variable overrides/degradation | Sources lacking this depth must degrade or use an explicitly approved variable-specific shorter rule |

## Proposed V1 calibration for approval

| Frequency | 1-5d | 1-3m | 1-3y | 3-10y |
|---|---|---|---|---|
| Monthly level/flow series | Source-specific applicability; do not manufacture daily signal | Latest complete month plus source-release gate; no 63-row requirement | 36 complete monthly observations (3 years) | 120 complete monthly observations (10 years) |
| Monthly derived 12-month statistic | Same | At least 24 months including warmup | At least 48 months including warmup | At least 132 months including warmup |
| Quarterly series | Usually `NOT_APPLICABLE` | Usually `NOT_APPLICABLE` | 12 complete quarters | 40 complete quarters |

The 120-month rule is a proposed structural minimum, not a claim that ten years guarantees predictive validity. It prevents the current 63-year artifact while retaining a materially longer sample than a single horizon comparison. Derived statistics add their warmup explicitly rather than hiding it in a row count.

## Guardrails

1. Replace row-count semantics only after each variable's evidence quantity and calendar unit are confirmed.
2. A shorter history may produce a score only if the variable-specific rule says it is economically meaningful; otherwise emit `INSUFFICIENT_DATA` with confidence zero.
3. Never fill missing months/quarters by compressing adjacent observations.
4. Do not alter frozen strategy weights, signs, or source contracts in this step.
5. Step 3 must add boundary tests at one observation below and exactly at each proposed minimum, plus missing-period tests.

## Approved decisions

- Ordinary monthly series: 36/120 complete months.
- Derived 12-month statistics: 48/132 months including warmup.
- Quarterly global defaults: 12/40 complete quarters, with explicit variable-specific overrides or degradation.
- Slow macro variables such as L4/L5 are `NOT_APPLICABLE` on 1-5d; faster monthly flows such as L8-001 retain release-gated applicability.
