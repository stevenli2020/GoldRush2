# DR3 — Data Analytics

DR3 combines current variable signals into one score, confidence level, and availability measure for each horizon.

Canonical implementation:

- [`SIGNAL_AUDIT.md`](SIGNAL_AUDIT.md) — findings, reference scores, evidence locations, repeatable verification methods, and Plan 1 closure.
- [`../PLAN2.md`](../PLAN2.md) — proposed source-semantic correction tasks awaiting review.

- [`config/weights_v1.yaml`](config/weights_v1.yaml) — versioned variable weights.
- [`src/goldrush2/dr3/analytics/`](src/goldrush2/dr3/analytics/) — aggregation models and engine.
- [`src/goldrush2/dr3/analyze.py`](src/goldrush2/dr3/analyze.py) — `gr2 analyze` command.
- [`data/current_scores.json`](data/current_scores.json) — latest output.
- [`config/strategies/`](config/strategies/) — immutable sparse current-outlook strategy configurations.
- [`data/current/dr3_multi_strategy_outlook.json`](data/current/dr3_multi_strategy_outlook.json) — non-official comparison output from `gr2 analyze-strategies`.
- [`SCORE_DELTA_REPORT.md`](SCORE_DELTA_REPORT.md) — fixed initial-matrix versus current-run audit comparison.
- [`PLAN2_STEP4_L4_COMPARISON.md`](PLAN2_STEP4_L4_COMPARISON.md) — controlled pre/post comparison for the L4-001 refresh.
- [`tests/`](tests/) — analytics tests.

The approved V1.1 design rationale is in [`DR3_PROPOSAL_zh.md`](DR3_PROPOSAL_zh.md). Plan 2 source-rule work remains proposed; run `gr2 analyze` after the required DR2 extractors have produced current JSON outputs.

`gr2 analyze-strategies` evaluates all 14 sparse strategies and the `SP-ALL` baseline from current DR2 signals only. It does not rank or select a strategy and does not change the existing official-score path.

Each horizon now includes `contributions` keyed by variable ID: configured `weight`, stored numeric `signal` and `confidence` (null for missing/non-numeric/non-finite values), `contribution` in score points, `input_status`, `reason`, and source `evidence_summary`. Status is VALID, MISSING, INVALID, INAPPLICABLE, UNAVAILABLE, or STALE. STALE is identified from the source evidence on zero-confidence inputs, not inferred from observation age. Unreadable files appear as missing usable data; the loader logs the parse failure.

`usable_weight_coverage` is the sum of VALID configured weights divided by all configured weights, including valid neutral inputs and excluding inapplicable/degraded inputs. It is not a confidence-weighted percentage and does not rescale scores. A horizon is `VALID` at coverage of 70% or greater and `DEGRADED` below that threshold. A strategy is `VALID` only when all four of its horizons are valid.

Scoring is fixed at `100 * weight * signal * confidence` for VALID inputs. Confidence zero is a hard gate: its contribution is exactly zero. A confidence strictly between zero and one is linear soft decay. The configured-weight denominator is never changed: zeroed or decayed weight remains unallocated. `warnings` lists excluded positive-weight inputs and available source explanations. Sum contributions and round to six decimals to reconcile to `score`.
