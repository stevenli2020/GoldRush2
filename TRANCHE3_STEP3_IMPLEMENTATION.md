# Tranche 3 Step 3 — Implementation

**Status:** implemented; awaiting controlled-refresh authorization

## Delivered

- Ordinary monthly minimums are 36 observations for `1-3y` and 120 for `3-10y`.
- Derived monthly 12-month statistics use 48 and 132 observations, including warm-up.
- Quarterly shared defaults are 12 observations for `1-3y` and 40 for `3-10y`; exact-boundary observations are accepted.
- Existing `1-3m` monthly behavior remains source-specific (63 observations where the extractor uses the shared WGC rule); Tranche 3 changes only the approved long-horizon minimums.
- L4-001 retains its derived-statistic 48/132 rules.
- L6-001 now uses the explicit Caldara-Iacoviello source vintage from collector metadata, ignores `retrieved_at` and filesystem mtime, applies a seven-day Monday/next-business-day freshness tolerance, and marks long horizons `NOT_APPLICABLE`.

## Verification

The focused Tranche 3 suite covers exact 35/36, 119/120 monthly boundaries, 11/12 and 39/40 quarterly boundaries, Monday and Tuesday-after-holiday freshness, missing-vintage degradation, and provenance isolation. The focused run passed 19 tests (with the pre-existing network snapshot-fallback test excluded).

The full WSL suite was executed on 2026-09-06: **808 passed, 30 failed**. The complete failure inventory is:

- `test_l0_002.py`: 2 long-horizon lookback cases.
- `test_l0_003.py`: 2 long-horizon lookback cases.
- `test_l0_005.py`: 4 quarterly lookback cases.
- `test_l0_006.py`: 4 quarterly lookback cases.
- `test_l5_001.py`: 2 long-horizon lookback cases.
- `test_l5_002.py`: 2 long-horizon lookback cases.
- `test_l5_003.py::test_signal_directions[59-59-0]`: exact quarterly boundary expectation.
- `test_l5_006.py`: 2 long-horizon lookback cases.
- `test_l6_001.py::test_snapshot_fallback`: network-sensitive fallback assertion; unrelated to window calibration.
- `test_l7_003.py::test_signal_directions[20-20-0]`: exact quarterly boundary expectation.
- `test_l8_001.py`: 2 long-horizon lookback cases.
- `test_l9_004.py`: 6 quarterly lookback/date expectation cases.
- `DR3_data_analytics/tests/test_aggregator.py::test_cli_analyze_command`: subprocess cannot resolve `gr2` under the test PATH; environment/fixture issue.

The 27 extractor failures are stale assertions against the superseded 252/756-month and 4/20-quarter contracts (with exact-boundary cases now intentionally accepted). The proposed disposition is to update those tests to assert 36/120, 12/40, and the new exact-boundary outputs; retain the snapshot fallback test as a separately quarantined live-network test; and fix the CLI test fixture to install/add the project command to PATH. No failure is being silently waived, and Step 4 remains blocked until D/Q approve this disposition and the suite is green or explicitly quarantined by policy.

## Scope boundary

No controlled source refresh or `gr2 analyze-strategies` rerun was performed in Step 3. Those actions belong to Tranche 3 Step 4 and require authorization.
