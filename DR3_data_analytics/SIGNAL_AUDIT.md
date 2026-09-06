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

## Reference score table supplied by the owner

This is the reviewed snapshot, not a forecast accuracy test. Input files can subsequently be overwritten by normal extraction. Future results need not reproduce these values unless their inputs are the same.

| Strategy | 1-5d | 1-3m | 1-3y | 3-10y |
|---|---:|---:|---:|---:|
| SP-RATE | -60 | -70 | -80 | -60 |
| SP-USD | 40 | 30 | -80 | 35 |
| SP-INFL | -50 | -80 | -60 | -60 |
| SP-CB | 60 | -70 | 60 | -15 |
| SP-FLOW | 70 | -70 | 60 | -20 |
| SP-TECH | 50 | 60 | 30 | 65 |
| SP-REGIME-PROXY | 10 | -10 | -35 | -32 |
| SP-ANTI-FIAT | 40 | -20 | 80 | 40 |
| SP-MACRO | -10 | -30 | -50 | -20 |
| SP-L0L5 | 60 | -10 | 60 | -10 |
| SP-L6L7 | 10 | 50 | -40 | 15 |
| SP-SPARSE | 40 | 0 | 10 | 0 |
| SP-SHORT | 70 | -20 | 5 | -40 |
| SP-LONG | 60 | -20 | -10 | -40 |
| SP-ALL | 2.2 | 2.2 | 2.2 | -8.9 |

Concentration explains part of the divergence: SP-RATE assigns 60% to an all-bearish real-yield signal, while SP-TECH assigns 60% to an all-bullish positioning signal. These are competing hypotheses, not independent forecasts to vote on. A score of +70 is neither a 70% probability nor a predicted return. The owner's bearish short-term/bullish long-term market impression motivates investigation; it is not a target for weight tuning.

## Evidence locations

Paths below are relative to the project root.

- Current inputs: `DR2_data_extraction/data/current/<variable ID>.json`.
- Monthly observation counting: `DR2_data_extraction/src/goldrush2/dr2/extractors/_wgc_common.py`, `HORIZON_LOOKBACKS` and `build_output`.
- CPI sign and acceleration wording: `DR2_data_extraction/src/goldrush2/dr2/extractors/l4_001.py`, `_valid` and `build_output`.
- Weekly liquidity counting: `DR2_data_extraction/src/goldrush2/dr2/extractors/l7_001.py`.
- Fiscal counting/applicability: `DR2_data_extraction/src/goldrush2/dr2/extractors/l4_006.py`.
- Premium units/cadence wording: `DR2_data_extraction/src/goldrush2/dr2/extractors/l9_001.py`.
- Stale GPR signal retention: `DR2_data_extraction/src/goldrush2/dr2/extractors/l6_001.py`.
- Fixed comparison arithmetic: `DR3_data_analytics/src/goldrush2/dr3/analytics/multi_strategy.py`, `_current_signal` and `run_multi_strategy`.
- Separate official confidence-weighted arithmetic: `DR3_data_analytics/src/goldrush2/dr3/analytics/aggregator.py`.
- Contract and governance: `PROJECT.md`; immutable strategies: `DR3_data_analytics/config/strategies/`.

The two aggregation commands use different formulas as well as different weights. Their differences cannot be attributed to strategy weights alone.

## Repeatable verification methods

### A. Inspect without changing production outputs

```bash
cd /mnt/d/Projects/GoldRush2
source .venv/bin/activate
python -m goldrush2.dr3.analytics.signal_audit
```

Verified during the audit: this prints all 11 input records across 44 horizons and 56 contribution rows for the 14 sparse strategies. Check actual observation and comparison dates, units, warnings, confidence and contribution size. The output shows existing behavior, including defective behavior; successful execution is not a validity certificate.

For any suspicious contribution, open the corresponding current JSON and extractor. Trace source quantity -> selected observation dates -> difference -> directional rule -> configured weight -> score points. Verify the arithmetic independently with `100 * weight * signal`, then sum the contributions. Keep missing/inapplicable inputs distinct from a valid neutral signal in the review notes.

### B. Existing automated checks

```bash
pytest DR3_data_analytics/tests/test_multi_strategy.py -q
pytest DR3_data_analytics/tests -q
pytest DR5_operations/tests/test_cli_extract.py -q
```

Earlier implementation runs reported 15 DR3 tests and 6 CLI tests passing. These are historical results, not fresh results from this documentation change. The present sparse tests cover basic configuration sums, unknown IDs, missing horizons, negative weights, the active count cap, Q's corrected SP-SHORT allocation, and some output fields. They do not establish source freshness, source semantics, frequency correctness or predictive power.

Known test limitations: the empty-input test checks only that `_current_signal` returns zero; despite its name, it does not test weight renormalization. The output test reads local current data and asserts 45 ADMIT variables, although the specification allows the production count to change. It verifies four horizons only for SP-RATE. The existing analytics CLI test invokes `gr2 analyze` and overwrites the official current-score file. Do not treat the full suite as read-only. No reliable full-suite result was captured for the sparse implementation's final broad run; do not report it as passing.

### C. Regenerate current comparisons intentionally

```bash
gr2 analyze-strategies
```

This reads stored signals and overwrites `DR3_data_analytics/data/current/dr3_multi_strategy_outlook.json`. It does not refresh collectors. Check 15 strategy entries, all four horizons for every strategy, `official_strategy: null`, no ranking, and experimental/baseline eligibility false. Verify contributions against the input JSON used in that run; running extraction between checks changes the evidence.

`gr2 analyze` separately overwrites `DR3_data_analytics/data/current_scores.json` using `config/weights_v1.yaml` under DR3. It does not select one of the sparse strategies.

### D. Source verification before signal correction

For each variable, record the exact source series or workbook sheet, unit, reporting frequency, latest published observation and release date when available. Compare the cached value and date to that source. Distinguish an observation date from its publication date and local download time. Inspect actual date spacing and missing periods, rather than trusting `data_frequency` or file modification time. Verify whether revisions and missing countries/funds affect aggregates. A stale-looking observation remains fresh when the source confirms it is the latest published observation, per PROJECT.md.

This live-source verification remains pending. Do not use the current audit to certify a cache as fresh or a source value as correct.

### E. Required regression cases for the correction work (not yet implemented)

| Case | Expected evidence or behavior |
|---|---|
| Same dates represented daily, weekly and monthly | Approved calendar targets drive selection; daily row counts are not reused blindly. |
| Missing month, holiday and duplicate date | Explicit handling under the approved method; no hidden shift in the economic window. |
| Exactly enough versus one too few observations | Correct boundary and comparison date; no off-by-one substitution. |
| CPI rises while its inflation rate falls | Evidence distinguishes disinflation from a declining price level; no unsupported acceleration claim. |
| Positive flows decline; negative flows improve | Distinguish inflow/outflow from acceleration/deceleration and use the approved gold-direction rule. |
| Cumulative holdings index given a different starting offset | Avoid interpreting offset-dependent percentages as changes in absolute holdings. |
| Stale +1 with confidence 0 | No usable directional contribution; explicit stale/missing reason retained. |
| Missing file, null signal, invalid signal | Clear degradation; never silently presented as fully observed neutrality. |
| Structural inapplicability versus valid zero | Distinct applicability and usable-data reporting under the agreed fixed-weight policy. |
| Mixed positive/negative contributions | Contribution sum reconciles exactly to score, allowing documented rounding. |
| Fractional confidence | Show the field; do not silently change the frozen scoring equation. |
| Production pool changes from 45 | Baseline uses the actual production registry and reports count. |
| All 15 strategies/all horizons | Output contract checked comprehensively; no ranking or automatic selection. |
| Official-score isolation | Comparison run leaves official output bytes unchanged; compare bytes directly without hashes. |

After approved corrections, run focused tests, refresh affected current inputs, rerun the unchanged strategies and explain each changed score through contributions. Preserve a concise dated decision/test record in documentation; no historical scoring system or backtest infrastructure is proposed.

## Decision and status record

- Sparse implementation: `c84b5f0`; owner fully approved the implementation. This does not validate economic predictiveness.
- Q corrected SP-SHORT 1-3y L8-001 from 0.20 to 0.25; other strategy weights remain frozen.
- Initial audit/tool: `aaeb70c`; diagnostics executed successfully in WSL.
- Frequency/source checks, economic method decisions, degradation corrections and post-correction scoring remain open.
- CPI channel remains the first economic decision. No new signs, thresholds or lookbacks have been approved through this audit.
