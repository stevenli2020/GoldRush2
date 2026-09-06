# Plan 2 Step 2 — Evidence Rules Draft

**Status:** draft submitted for D/Q review; not approved for implementation
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

### Quantitative mapping supplied by Q

The draft records the locked anchors exactly as supplied:

- `2.5%` is the neutral anchor.
- `> 4.0%` maps to `+1`.
- `2.5%–4.0%` maps to `+0.5` as an intermediate positive state.
- `< 1.5%` maps to `-1`.

The following two points require explicit D/Q resolution before coding:

1. The `2.5%` neutral anchor overlaps the stated `2.5%–4.0% -> +0.5` interval.
2. The interval `1.5%–2.5%` has no supplied mapping.

No interpretation is silently added here. The final rule sheet must state whether the boundary is inclusive and what signal applies to the unresolved interval. The current CPI level-change rule is not approved for reuse.

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

Step 3 may begin only after D/Q approves the source contract and evidence rule for each variable being changed. Approval must explicitly resolve L4-001's two threshold gaps and confirm the publication-date fields and release-lag cutoff. Frozen strategy weights, Plan 1 gating, the 70% coverage threshold, and current-outlook-only scope remain unchanged.
