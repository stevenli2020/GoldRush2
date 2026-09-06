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

The full suite was started under WSL. Remaining failures are legacy assertions tied to the superseded long-horizon row counts, the intentionally network-sensitive snapshot fallback, and the known subprocess `gr2` PATH fixture. These must be resolved or explicitly accepted before Step 4 is run.

## Scope boundary

No controlled source refresh or `gr2 analyze-strategies` rerun was performed in Step 3. Those actions belong to Tranche 3 Step 4 and require authorization.
