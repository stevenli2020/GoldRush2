# Sparse signal audit and correction sequence

2026-09-06. Status: initial audit completed; economic rule corrections proposed, not implemented.

## Scope and evidence

Reviewed the 11 distinct sparse-strategy inputs and their 44 current horizon outputs, the monthly WGC helper, CPI, fiscal, premium and GPR extractor rules, and the sparse aggregation formula. Stored evidence has not been independently refreshed against live sources. This audit does not establish prediction accuracy.

Run `python -m goldrush2.dr3.analytics.signal_audit` in the GR2 WSL environment for full nested evidence and 56 sparse-strategy horizon contribution breakdowns. It prints to standard output and does not refresh sources or overwrite production data. SP-ALL is outside this sparse-input audit; its broader 45-variable pool still needs a separate review before relying on the baseline.

## Findings across all sparse inputs

| Input | Current evidence and issue | Proposed treatment |
|---|---|---|
| L4-001 CPI | Monthly level compared with March 2026, April 2021, July 2005 and July 1963. An index increase is called accelerating inflation and always mapped bearish. | Separate price level, inflation rate and inflation acceleration. Decide the economic channel before choosing gold direction. |
| L8-001 ETF flows | July 2026 versus March 2026, May 2021 and August 2005. Long horizon requires 756 monthly observations. | Correct source-frequency handling. Distinguish signed net inflow from a change in flow; evaluate monthly and trailing-period flows as candidate evidence. |
| L5-001 official purchases | Same monthly row-count problem. Positive purchases versus an old higher purchase month produce bearish output. | Separate net buying/selling from acceleration; use a calendar-based evidence window and document release lag. |
| L7-001 Fed assets | Weekly data uses 5/63/252/756 rows; medium horizon compares September 2026 with June 2025. | Use weekly/calendar comparisons with explicit dates. Describe Fed liquidity, not all global liquidity. |
| L0-002 official holdings | Output is a cumulative net-change index, not an absolute holdings level. Same monthly lookbacks; percentages depend on an arbitrary cumulative origin. | Verify actual holdings availability; label index honestly, avoid index percentage changes, and examine overlap with L5-001. |
| L1-001 real yields | Daily comparisons are plausible as historical evidence; rising yields map bearish. | Verify source values and offset convention; describe opportunity-cost pressure rather than a validated multi-year forecast. |
| L2-001 dollar | Daily comparisons are plausible as historical evidence. | Verify source values/calendar gaps and retain explicit inverse-dollar rationale. |
| L4-006 fiscal balance | Label says quarterly; current evidence compares 2025 with 2018 and 2006. Short horizons lack explicit applicable=false. | Verify source frequency first; do not call annual observations quarters. Correct metadata and applicability before selecting windows. |
| L6-001 geopolitical | Short signals are +1 with confidence 0 and an explicit stale warning. Code uses deterministic GPR calculation although PROJECT.md describes this ID as Gemini-derived. | Enforce existing zero-confidence degradation contract; reconcile documented versus actual method before economic reinterpretation. |
| L9-001 premium | Label and text say weekly; five-observation comparison spans August 21-28. A USD change is stored as change_pct. | Verify workbook cadence; correct units and date language. Separate premium level from widening/narrowing. |
| L10-001 positioning | Weekly 5/13/52/260 comparisons; positive on all horizons. Deterministic confidence tapers 1/.8/.6/.4. | Review near-term lookback and long-horizon applicability. Resolve confidence policy against PROJECT.md. Keep experimental strategy eligibility unchanged. |

## Exact score implications

The existing engine counts stale L6-001 as +40 points in SP-L6L7 on both short horizons. The reported +10 and +50 therefore become -30 and +10 if only that unusable input contributes zero, with all weights and other inputs held constant. This is a diagnostic counterfactual, not a replacement production result.

SP-SHORT 1-5d is +70: real yields -5, dollar +20, Fed assets -10, ETF flows +35, premium +15, positioning +15. The ETF input supplying +35 compares July with March, so +70 cannot be read as a clean assessment of recent five-day conditions.

SP-SHORT 1-3m is -20: real yields -10, dollar +20, CPI -5, Fed assets +10, ETF flows -30, premium -15, positioning +10. The largest negative input compares July 2026 with May 2021.

The fixed scoring equation remains 100 * sum(weight * signal). Its output currently conceals missingness, confidence and applicability; neutral zero and missing zero cannot be distinguished in the score table. Confidence 1 means a deterministic rule ran, not 100% confidence in future price direction.

## Correction sequence and verification gates

1. Repair unusable-input handling and show per-variable contribution, usable configured weight, and explicit missing/stale/applicability reasons. Preserve frozen weights; do not silently renormalize or introduce a fractional-confidence multiplier. Test stale +1/confidence 0, missing JSON, null signals, structural neutrality and cancellation separately.
2. Verify source frequency and release dates for the four priority inputs (CPI, ETF flows, official purchases, Fed assets), then fiscal balance and premiums. Check latest data at source; snapshot age alone cannot prove staleness.
3. Write one explicit rule per variable/horizon: economic quantity, evidence window, minimum observations, gold-direction rationale, applicability and confidence. Calendar dates must accompany every comparison. Choose rules for their meaning, not their resulting sign. A lookback is evidence for an outlook, not the outlook itself.
4. Implement approved rules with fixtures that expose daily/monthly/weekly mismatches, missing calendar periods and off-by-one errors. Tests must check actual dates and meaning, not merely mirror row offsets.
5. Refresh the affected current signals and rerun the same frozen configurations. Explain changed scores by contribution; do not rank strategies or claim predictive validation from one snapshot.

The first economic decision is L4-001: should it represent the direct purchasing-power channel or inflation-driven policy pressure? Those can point in different directions. A positive CPI level change alone cannot resolve this. Exact CPI direction and horizon rules remain open for the owner/researchers; no unapproved threshold or sign reversal has been introduced.
