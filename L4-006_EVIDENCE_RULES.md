# L4-006 Evidence Rules — Draft for D Approval

**Status:** approved; directional rule active

## Causal channel

L4-006 measures federal deficit/surplus as a share of GDP. A widening deficit (a falling ratio) is mapped to a bullish gold signal because it represents increased fiat-credit and fiscal-credibility pressure. A narrowing deficit is mapped bearish. No monetary-policy expectation channel is included.

## Calculation and alignment

- Source: FRED `FYFSGDA188S`.
- Frequency: quarterly.
- Observation alignment uses the source observation date and explicit release metadata when available; retrieval time and filesystem mtime are not publication dates.
- Comparison windows are 12 complete quarters for `1-3y` and 40 complete quarters for `3-10y`.
- Missing or insufficient quarterly history is not compressed or backfilled.

## Directional mapping

Approved mapping: deficit/GDP falls → `+1`; rises → `-1`; unchanged → `0`. Valid horizons use confidence `1.0`; unsupported short horizons remain `NOT_APPLICABLE`.

## Degradation

Source unavailability, missing release evidence, stale cache, malformed observations, or insufficient history must produce `confidence=0` with an explicit `DEGRADED` or `INSUFFICIENT_HISTORY` status. No weight renormalization is permitted.
