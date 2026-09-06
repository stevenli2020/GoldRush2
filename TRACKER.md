# GR2 Development Tracker — Phase DR3 (Data Analytics)

## Roadmap Status
| Roadmap | Deliverable | Status |
|---|---|---|
| DR1 | Define the 11 layers and 45 variables | **Complete** |
| DR2 | Shared source collectors and one current extractor JSON per variable | **Complete** (45/45) |
| DR3 | Versioned fixed variable-weight schema and researched aggregation method | **Complete** |
| DR4 | Four current scores, confidence levels, and Gemini report | Not started |
| DR5 | One-command user workflow, inputs, outputs, and notifications | Not started |

## DR3 Task Tracker (Expert-Reviewed V1.1)
| Task ID | Task Description | Status | Notes |
|---|---|---|---|
| DR3-01 | Design & approve dynamic weight normalization logic | **Complete** | V1.1 formulas verified by focused tests and live scoring |
| DR3-02 | Create `DR3_data_analytics/config/weights_v1.yaml` | **Complete** | Valid YAML, structural omissions, excluded reserve-share proxy, and rationales verified |
| DR3-03 | Implement `DR3_data_analytics/src/goldrush2/dr3/analytics/aggregator.py` | **Complete** | Confidence-weighted score denominator, availability, applicability, and Top-5 monitoring verified |
| DR3-04 | Implement `DR3_data_analytics/src/goldrush2/dr3/analyze.py` & CLI registration | **Complete** | `gr2 analyze` help and live execution verified |
| DR3-05 | Write unit tests for missing-data degradation | **Complete** | Eight focused tests pass |
| DR3-06 | Verify end-to-end scoring with live DR2 data | **Complete** | Generated `DR3_data_analytics/data/current_scores.json`; live run completed successfully |
| DR3-07 | Implement frozen sparse strategy comparison | **Complete** | 14 sparse strategies plus `SP-ALL`; hard validation, `gr2 analyze-strategies`, and non-official current-only output verified |
| DR3-08 | Audit sparse-input semantics and contributions | **Complete; Plan 2 follow-up required** | See `DR3_data_analytics/SIGNAL_AUDIT.md`; 11 inputs/44 horizons reviewed, 56 sparse attribution rows available. Economic/source corrections are explicitly moved to proposed Plan 2. |
| DR3-09 | Plan 1 Step 1: gate unusable sparse inputs | **Approved; complete** | Zero-confidence/invalid/missing/inapplicable inputs contribute zero with stderr reasons; configured weights are not redistributed. |
| DR3-10 | Plan 1 Step 2: structured input diagnostics | **Approved; complete** | Per-variable contributions/status/reasons, usable-weight coverage and warnings. |
| DR3-11 | Plan 1 Step 3: regression verification | **Approved; complete** | 25 focused WSL tests passed, including cancellation, missing-horizon/malformed-file checks, byte-preservation through real CLI dispatch, and isolated output tests. |
| DR3-12 | Plan 1 Step 4: comparison, coverage status and delta record | **Approved; complete** | 27 focused WSL tests passed. Added Q's 70% coverage validity floor and fractional-confidence soft decay without renormalization; regenerated comparison and `SCORE_DELTA_REPORT.md` records 16 degraded results of 60. |
| DR3-13 | Plan 2 Task 1: source and frequency contract inventory | **Complete; submitted for review** | [`PLAN2_STEP1_SOURCE_CONTRACTS.md`](PLAN2_STEP1_SOURCE_CONTRACTS.md) inventories source, cadence, date behavior, release-lag gaps, and freshness-contract gaps. No extractor changes. |
| DR3-14 | Plan 2 Task 2: approve variable and horizon evidence rules | **Approved; complete** | [`PLAN2_STEP2_EVIDENCE_RULES.md`](PLAN2_STEP2_EVIDENCE_RULES.md) locks the L4-001 purchasing-power channel, publication-date cutoff, `CPI_YoY_12m_MA`, exact four-band mapping, and confidence-zero degradation rules. |
| DR3-15 | Plan 2 Task 3: implement frequency-aware extraction corrections | **Approved; L4-001 tranche complete** | [`PLAN2_STEP3_IMPLEMENTATION.md`](PLAN2_STEP3_IMPLEMENTATION.md) records publication-aligned `CPI_YoY_12m_MA`, exact thresholds, degradation logic, signal-contract compatibility, and tests. Other variables remain unchanged. |
| DR3-16 | Plan 2 Task 4: refresh, rerun, and review corrected outlook | **Approved; complete and archived** | P0 FRED metadata/stale-gating bug fixed, matrix regenerated, and approved by Q. See [`PLAN2_STEP4_P0_BUG_REPORT.md`](PLAN2_STEP4_P0_BUG_REPORT.md). |
| DR3-17 | Tranche 2 Step 1: WGC source contract inventory | **Approved; complete** | L8-001/L5-001 shared WGC collector contract, publication-date findings, revision/cadence gaps, and no-mtime rule in [`PLAN2_TRANCHE2_STEP1_WGC_SOURCE_CONTRACTS.md`](PLAN2_TRANCHE2_STEP1_WGC_SOURCE_CONTRACTS.md). |
| DR3-18 | Tranche 2 Step 2: WGC evidence-rule draft | **Approved; complete** | D/Q approved `wgc_schedule_bound_v1`, T+8/T+11, L5 1-5d `NOT_APPLICABLE`, and provenance-only page dates in [`PLAN2_TRANCHE2_STEP2_WGC_EVIDENCE_RULES.md`](PLAN2_TRANCHE2_STEP2_WGC_EVIDENCE_RULES.md). |
| DR3-19 | Tranche 2 Step 3: WGC extractor implementation | **Implemented; review required** | L8/L5 schedule-bound gating, status labels, metadata separation, and 54 focused WSL tests in [`PLAN2_TRANCHE2_STEP3_IMPLEMENTATION.md`](PLAN2_TRANCHE2_STEP3_IMPLEMENTATION.md). |
