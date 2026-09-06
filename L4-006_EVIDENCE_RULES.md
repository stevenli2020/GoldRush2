# L4-006 Evidence Rules — Draft for D Approval

**Status:** pending formal directional approval; production contribution disabled

## Causal channel

L4-006 measures federal deficit/surplus as a share of GDP. A widening deficit (a falling ratio) is mapped to a bullish gold signal because it represents increased fiat-credit and fiscal-credibility pressure. A narrowing deficit is mapped bearish. No monetary-policy expectation channel is included.

## Calculation and alignment

- Source: FRED `FYFSGDA188S`.
- Frequency: quarterly.
- Observation alignment uses the source observation date and explicit release metadata when available; retrieval time and filesystem mtime are not publication dates.
- Comparison windows are 12 complete quarters for `1-3y` and 40 complete quarters for `3-10y`.
- Missing or insufficient quarterly history is not compressed or backfilled.

## Directional mapping

Before approval, every horizon is forced to `signal=0`, `confidence=0`, `status=NOT_APPLICABLE`. The provisional proposed mapping is: deficit/GDP falls → `+1`; rises → `-1`; unchanged → `0`.

## Degradation

Source unavailability, missing release evidence, stale cache, malformed observations, or insufficient history must produce `confidence=0` with an explicit `DEGRADED` or `INSUFFICIENT_HISTORY` status. No weight renormalization is permitted.
