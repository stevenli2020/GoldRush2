# Plan 2 Step 2 — Evidence Rules Draft

**Status:** approved and closed by D/Q
**Date:** 2026-09-06
**Dependency:** [`PLAN2_STEP1_SOURCE_CONTRACTS.md`](PLAN2_STEP1_SOURCE_CONTRACTS.md)

## Global rule contract

For every variable and horizon, the extractor must record the measured quantity, source observation date, source `publication_date` when available, release lag, eligible evidence window, comparison observation, unit, applicability, directional rationale, and confidence rule. Eligibility is cut off at the decision timestamp using `publication_date`; an observation published later is unavailable to that run even if its observation period is earlier.

Insufficient history, missing required observations, stale data beyond the approved source-confirmed limit, unreachable source beyond cache allowance, parser failure, or unavailable credentials must produce signal `0`, confidence `0.0`, and a clearly labelled evidence summary. Structural inapplicability remains an intentional neutral result with confidence `1.0`.

## Locked L4-001 rule — CPI purchasing-power channel only

### Causal channel

L4-001 maps only **purchasing-power erosion** (“盾”). It must not map monetary-policy expectations (“雷”), policy repricing, real yields, or any other L1/L3 channel. Those channels are excluded to avoid double counting and causal contamination.

### Time alignment

The evidence window is selected using CPI observation records whose `publication_date` is on or before the decision timestamp. Release lag is handled by truncating the eligible set at that publication cutoff; an observation with a future publication date is not usable. The extractor must retain both the CPI reference period and publication date in `evidence.data`.

### Approved quantitative mapping and smoothing

The decision quantity is `CPI_YoY_12m_MA`, the 12-month moving average of CPI year-over-year inflation. CPI level may rise while the smoothed inflation rate falls; that is not a contradiction and must not introduce a policy-expectations or rate-pressure signal.

The approved discrete mapping is:

- `< 1.5%` → `-1.0`
- `[1.5%, 2.5%)` → `0.0`
- `[2.5%, 4.0%)` → `+0.5`
- `>= 4.0%` → `+1.0`

The boundaries are inclusive/exclusive exactly as written. The current CPI index-level comparison and its “accelerating inflation” interpretation are not approved for reuse. No policy-expectations, rate-hike, real-yield, or L3 channel may be introduced into L4-001.

### Degradation

If the required publication-aligned CPI history is insufficient, if the latest eligible publication is beyond the approved freshness limit without source confirmation, or if the source is unreachable beyond cache allowance, return `signal=0`, `confidence=0.0`, and a summary beginning `INSUFFICIENT HISTORY` or `STALE DATA` as applicable.

## Draft rules for the remaining priority variables

These are scaffolds for review, not implementation authorization.

| Variable | Quantity to preserve | Evidence/date requirement | Rule status |
|---|---|---|---|
| L0-002 | Official-changes flow/index, not an absolute holdings level | Monthly publication-aligned windows; disclose cumulative-origin dependence | Needs D/Q approval |
| L1-001 | 10Y TIPS real yield and opportunity-cost direction | Daily observation and publication/release timing; market holidays explicit | Needs D/Q approval |
| L2-001 | DXY level/change | Market-session timestamps and time zone; no hidden future rows | Needs D/Q approval |
| L4-006 | Fiscal balance/GDP | Quarterly period and release date; short horizons structurally inapplicable | Needs D/Q approval |
| L5-001 | Official-sector net purchases | Monthly publication-aligned windows; separate level from acceleration | Needs D/Q approval |
| L6-001 | Geopolitical signal under the reconciled method | Daily source date, publication/freshness behavior, long-horizon applicability | Needs D/Q approval |
| L7-001 | Federal Reserve total assets/liquidity proxy | Weekly publication-aligned windows and release weekday | Needs D/Q approval |
| L8-001 | ETF net flows, not an unlabelled flow acceleration | Monthly period end and publication lag; distinguish flow from change in flow | Needs D/Q approval |
| L9-001 | China physical premium level/change with declared unit | Weekly workbook period/publication date; USD/oz and percentage remain distinct | Needs D/Q approval |
| L10-001 | CFTC managed-money net positioning | Tuesday observation versus Friday publication; long-horizon confidence/applicability explicit | Needs D/Q approval |

## Approval gate for Step 3

Step 3 may begin under this approved L4-001 rule. The extractor must use `publication_date`—never `reference_date`—for eligibility and release-lag cutoffs, calculate `CPI_YoY_12m_MA`, and preserve the locked causal channel and thresholds. Frozen strategy weights, Plan 1 gating, the 70% coverage threshold, and current-outlook-only scope remain unchanged.
