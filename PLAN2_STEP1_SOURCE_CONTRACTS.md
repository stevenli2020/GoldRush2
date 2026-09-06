# Plan 2 Step 1 — Source and Frequency Contract Inventory

**Status:** completed for review  
**Date:** 2026-09-06  
**Scope:** repository-backed inventory only; no source refresh or extractor change was performed.

## Contract rules carried into Step 2

- `publication_date`, when supplied by the source, is the date used to decide whether an observation was available for an outlook run.
- `observation_date` describes the period measured; it is not a substitute for publication date.
- Release lag must truncate each horizon's eligible observations at the run's decision timestamp. Future-published observations must not enter an earlier outlook.
- Freshness is variable-specific. A source-confirmed latest observation may remain fresh beyond its normal interval; an unreachable source may use cache only within that variable's approved limit.
- The current extractor JSON does not yet carry `publication_date` consistently. That is a Plan 2 implementation gap, not an assumption that publication and observation dates are equal.

## Priority inventory

| Variable | Current source in code | Current frequency | Current date/lookback behavior | Contract gap to resolve |
|---|---|---|---|---|
| L0-002 | WGC/IMF IFS official changes; [WGC](https://www.gold.org/) | Monthly | Uses monthly rows through `HORIZON_LOOKBACKS` 5/63/252/756; cumulative index from first available month | Confirm publication date, revision policy, and whether cumulative changes are valid evidence for each horizon |
| L1-001 | FRED DFII10; [FRED](https://fred.stlouisfed.org/series/DFII10) | Not declared in output; source is daily | Uses source rows for 5/63/252/756 comparisons | Add source cadence and publication/release timestamp; define holiday and release-day handling |
| L2-001 | Yahoo Finance DX-Y.NYB; [Yahoo Finance](https://finance.yahoo.com/quote/DX-Y.NYB/) | Not declared in output; source is market-day series | Uses source rows for 5/63/252/756 comparisons | Confirm timestamp/time zone, missing market days, and whether row count represents the intended calendar window |
| L4-001 | FRED CPIAUCSL; [FRED](https://fred.stlouisfed.org/series/CPIAUCSL) | Monthly | Currently applies 5/63/252/756 row lookbacks | Add release/publication date and enforce the approved purchasing-power rule; never infer policy expectations from CPI level |
| L4-006 | FRED FYFSGDA188S; [FRED](https://fred.stlouisfed.org/series/FYFSGDA188S) | Quarterly | 1-3y uses 8 quarters; 3-10y uses 20 quarters; short horizons are inapplicable | Confirm fiscal-year period and release dates; preserve explicit short-horizon inapplicability |
| L5-001 | WGC/IMF IFS official-sector purchases; [WGC](https://www.gold.org/) | Monthly | Uses monthly rows through 5/63/252/756 comparisons | Confirm publication lag, revisions, aggregate construction, and purchase-versus-change meaning |
| L6-001 | GPRD_ACT; [Caldara–Iacoviello](https://www.matteoiacoviello.com/gpr.htm) | Daily | Requires 60 observations; short horizons only; long horizons disabled | Reconcile documented Gemini-derived definition with actual GPR implementation and define publication/freshness semantics |
| L7-001 | FRED WALCL; [FRED](https://fred.stlouisfed.org/series/WALCL) | Weekly | Currently applies 5/63/252/756 row lookbacks | Confirm release weekday/time, holiday gaps, and calendar-based horizon mapping |
| L8-001 | WGC global gold ETF flows; [WGC](https://www.gold.org/) | Monthly | Currently applies 5/63/252/756 row lookbacks | Confirm publication date, monthly period end, revisions, and flow versus flow-change quantity |
| L9-001 | WGC China premium workbook; [WGC gold premium](https://www.gold.org/goldhub/data/gold-premium) | Weekly | Currently applies 5/63/252/756 row lookbacks | Confirm workbook publication date, weekly period convention, USD/oz versus percentage units, and missing-week handling |
| L10-001 | CFTC Disaggregated COT; [CFTC](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) | Weekly | Uses 5/13/52/260 rows with confidence 1.0/0.8/0.6/0.4 | Confirm Tuesday observation versus Friday publication timing and the approved long-horizon applicability rule |

## Findings

1. Monthly, weekly, and daily extractors currently reuse row-count lookbacks across all four horizons. This is the principal frequency-contract defect identified for Plan 2.
2. Current JSON generally records `observation_date` and local `as_of_date`, but not source `publication_date`. Release lag therefore cannot yet be audited from the JSON contract.
3. The inventory confirms the sources and frequencies used by the current code; it does not certify that any source is reachable, current, or economically fit.
4. The exact source contract and evidence rule must be approved before Step 3 changes code.

## Step 2 handoff

The proposed evidence rules are in [`PLAN2_STEP2_EVIDENCE_RULES.md`](PLAN2_STEP2_EVIDENCE_RULES.md). L4-001 includes Q's locked causal channel and threshold requirements, with two arithmetic ambiguities called out for D/Q resolution rather than silently guessed.
