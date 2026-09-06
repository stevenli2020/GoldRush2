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

The rectified WSL suite was executed with the quarantined network tests excluded:

```text
.venv/bin/pytest -q -k "not snapshot_fallback"
836 passed, 2 deselected, 851 warnings
```

The two deselected tests are exactly the two tests listed in [`TEST_QUARANTINE.md`](TEST_QUARANTINE.md). No other tests failed, and no undocumented anomaly was observed in this run.

The superseded failure inventory that led to this rectification was:

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

The 28 extractor failures are stale assertions against the superseded 252/756-month and 4/20-quarter contracts (with exact-boundary cases now intentionally accepted). The earlier report called this 27; the omitted 28th extractor failure was `DR2_data_extraction/tests/test_l7_003.py::test_signal_directions[20-20-0]`, which has the same root cause: its fixture still supplies the old 20-quarter boundary. Proposed disposition: update all affected assertions to 36/120, 12/40, and the new exact-boundary outputs; retain the snapshot fallback test under the quarantine record; and fix the CLI test fixture to install/add the project command to PATH. No failure is being silently waived.

## Boundary-test spot check

The new tests are not number-only edits. They construct exactly N dated observations, call the production builders, and assert the production confidence gate:

```python
# monthly_rows(35/36/119/120) -> L8 production builder
below_36 = l8_001.build_output(..., monthly_rows(35), as_of_date="2100-01-01")
at_36 = l8_001.build_output(..., monthly_rows(36), as_of_date="2100-01-01")
below_120 = l8_001.build_output(..., monthly_rows(119), as_of_date="2100-01-01")
at_120 = l8_001.build_output(..., monthly_rows(120), as_of_date="2100-01-01")
assert below_36["horizons"]["1-3y"]["confidence"] == 0
assert at_36["horizons"]["1-3y"]["confidence"] == 1
assert below_120["horizons"]["3-10y"]["confidence"] == 0
assert at_120["horizons"]["3-10y"]["confidence"] == 1
```

```python
# quarterly_rows(11/12/39/40) -> shared production quarterly builder
assert build(quarterly_rows(11))["horizons"]["1-3y"]["confidence"] == 0
assert build(quarterly_rows(12))["horizons"]["1-3y"]["confidence"] == 1
assert build(quarterly_rows(39))["horizons"]["3-10y"]["confidence"] == 0
assert build(quarterly_rows(40))["horizons"]["3-10y"]["confidence"] == 1
```

The production quarterly gate is `len(ordered) < lookback`, so N-1 is degraded and N is accepted; the monthly gate follows the same minimum-observation contract in the shared WGC builder.

## Scope boundary

No controlled source refresh or `gr2 analyze-strategies` rerun was performed in Step 3. Those actions belong to Tranche 3 Step 4 and require authorization.
