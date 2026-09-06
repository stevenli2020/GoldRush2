# Plan 2 Step 3 — Frequency-Aware Extractor Corrections

**Status:** L4-001 first tranche implemented; review required
**Scope:** L4-001 only, plus shared FRED metadata preservation. Other variables remain unchanged.

## Implemented rule

- L4-001 uses the purchasing-power channel only.
- The decision quantity is `CPI_YoY_12m_MA`.
- Monthly observations are eligible only when their source `publication_date` is on or before the decision date. `reference_date`/observation date is never used as a publication substitute.
- FRED `realtime_start` is vintage metadata, not a publication date, and is preserved only as `vintage_date` for provenance. It is never used for publication alignment or freshness. If no explicit publication metadata exists, the observation is not eligible and the output is conservatively degraded.
- The exact approved mapping is `<1.5 -> -1.0`, `[1.5,2.5) -> 0.0`, `[2.5,4.0) -> +0.5`, and `>=4.0 -> +1.0`.
- DR3 accepts the approved discrete signal set `-1`, `-0.5`, `0`, `+0.5`, and `+1`; the L4-001 `+0.5` output is therefore not discarded as invalid.
- Insufficient publication-aligned history and evidence observation age beyond 62 days return signal `0`, confidence `0.0`, with an explicit degradation summary. The 62-day limit represents two monthly release intervals for this tranche and remains variable-specific.
- All four horizons use the latest eligible smoothed CPI evidence; no policy-expectations or rate-pressure logic is introduced.

## Required test coverage delivered

- Exact boundaries: `1.49%`, `1.50%`, `2.49%`, `2.50%`, `3.99%`, `4.00%`.
- CPI level rising while the smoothed inflation rate is not rising.
- Future publication excluded until its publication date.
- Missing publication metadata and insufficient history produce confidence zero.
- Stale evidence observation period produces confidence zero.
- FRED vintage metadata is not treated as publication metadata.

## Verification

- Target L4-001 suite: 16 tests passed.
- Affected FRED/L4 compatibility suite: 142 tests passed.
- Full DR3 analytics suite after the signal-contract correction: 36 tests passed.
- Full DR2 suite: 783 passed, 1 unrelated pre-existing failure in `DR2_data_extraction/tests/test_l6_001.py::test_snapshot_fallback` (GPR collector fallback). No L4/FRED test failed.

## Review boundary

This tranche does not modify strategy weights, DR3 gating, other extractors, source collectors, or the current outlook output. Before expanding Step 3 to other variables, approve their source publication contracts and evidence rules separately.
