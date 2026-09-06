# GR2 Plan 2 — Source-Semantic Corrections

## Status

Archived after owner/Q approval of the P0 L4-001 metadata/stale-gating correction. The incident record is [`PLAN2_STEP4_P0_BUG_REPORT.md`](PLAN2_STEP4_P0_BUG_REPORT.md). Tranche 2 Step 1 is authorized; its draft contracts are [`PLAN2_TRANCHE2_STEP1_WGC_SOURCE_CONTRACTS.md`](PLAN2_TRANCHE2_STEP1_WGC_SOURCE_CONTRACTS.md) and [`PLAN2_TRANCHE2_STEP2_WGC_EVIDENCE_RULES.md`](PLAN2_TRANCHE2_STEP2_WGC_EVIDENCE_RULES.md).

## Objective

Improve the meaning and timeliness of DR2 current signals without changing the frozen sparse strategy configurations, adding historical replay, or tuning signs to obtain a preferred market result.

The immediate evidence is documented in [`DR3_data_analytics/SIGNAL_AUDIT.md`](DR3_data_analytics/SIGNAL_AUDIT.md) and [`DR3_data_analytics/SCORE_DELTA_REPORT.md`](DR3_data_analytics/SCORE_DELTA_REPORT.md). The current comparison remains a stored-data diagnostic, not a validated forecast.

## Proposed tasks

### Plan 2 Task 1 — Source and frequency contract inventory

For each priority variable, record the exact public source series or workbook sheet, unit, publication cadence, observation-date convention, release lag, revision behavior, and source-confirmed freshness rule. Start with L4-001, L8-001, L5-001, and L7-001; then cover L4-006, L9-001, L0-002, L10-001, and L6-001 as needed.

Deliverable: [`PLAN2_STEP1_SOURCE_CONTRACTS.md`](PLAN2_STEP1_SOURCE_CONTRACTS.md), a source contract table linked to each variable. This task is read-only and did not alter current JSON or extractor behavior.

### Plan 2 Task 2 — Variable and horizon evidence-rule approval

For every priority variable and horizon, specify the economic quantity being measured, calendar-based evidence window, minimum observations, applicability, direction rationale, confidence rule, and release-lag treatment. Keep source facts, annotations, and interpretation separate. Do not infer a sign from the desired aggregate outcome.

Deliverable: [`PLAN2_STEP2_EVIDENCE_RULES.md`](PLAN2_STEP2_EVIDENCE_RULES.md), now approved and closed by D/Q. Step 3 may implement the locked L4-001 rule without changing its causal channel or thresholds.

### Plan 2 Task 3 — Frequency-aware extractor implementation

Implement only the approved rules in Python. Add fixtures and focused tests for daily, weekly, and monthly calendars; holidays and missing periods; exact boundary counts; units; revisions; and source-confirmed latest observations. Preserve the one-current-JSON-per-variable contract and the existing stale/missing-data labels.

Deliverable: corrected extractors, tests, and a verification record. The L4-001 first tranche is documented in [`PLAN2_STEP3_IMPLEMENTATION.md`](PLAN2_STEP3_IMPLEMENTATION.md). Frozen strategy weights and Plan 1 gating remain unchanged.

### Plan 2 Task 4 — Controlled refresh and comparison review

Refresh only the affected sources, regenerate their current JSON, run `gr2 analyze-strategies`, and explain every material score change through the structured contributions and coverage/status fields. Update the delta report and tracker. Do not rank strategies or claim predictive accuracy from the refreshed snapshot.

Deliverable: reviewed post-correction comparison and an owner decision on the next correction tranche.

The L4-001 tranche is closed. Tranche 2 now begins with source-contract and evidence-rule drafts for L8-001 and L5-001 through their shared monthly WGC collector. No extractor implementation or refresh is authorized until D/Q approve the drafts.

## Acceptance gates

- No Plan 2 implementation starts without approval of the relevant source contracts and evidence rules.
- No change to frozen strategy weights, horizon definitions, or current-outlook-only scope.
- Every corrected signal has source provenance, explicit dates, units, applicability, and a concise evidence summary.
- Tests prove calendar/frequency behavior and preserve hard gating, soft confidence decay, fixed denominators, and the 70% coverage status threshold.
- Live-source failures remain distinguishable from cache fallback, stale data, credential failures, and parser failures.

## Deferred items

The CPI channel, geopolitical method alignment, long-horizon interpretation of flows/positioning, and any future dynamic weighting remain owner decisions. Plan 2 does not introduce regime switching, backtesting, hashing, or additional indicators.
