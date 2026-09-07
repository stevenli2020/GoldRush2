# Tranche 2 Step 4 — Controlled Refresh and Comparison Review

**Status:** completed; review/closure required
**Scope:** L8-001 ETF flows and L5-001 official-sector purchases only
**Run date:** 2026-09-06

## Controlled refresh

Only `gr2 extract L8-001` and `gr2 extract L5-001` were executed. The WGC source was reachable and the extractors produced current JSON without a cache-fallback warning.

| Variable | Latest observation | Estimated availability | Decision date | Result |
|---|---|---|---|---|
| L8-001 | 2026-07-31 | 2026-08-08 (month-end + 8 days) | 2026-09-06 | Activated; `confidence=1.0` |
| L5-001 | 2026-07-01 (July reference month) | 2026-08-11 (month-end + 11 days) | 2026-09-06 | Activated; August remains pending until 2026-09-11 |

Both outputs retain `publication_date: null`. The schedule bound is recorded only as `estimated_availability_date` with `availability_source: wgc_schedule_bound_v1`. `source_page_date` remains null and `retrieved_at` is provenance only.

L5-001 1-5d is `NOT_APPLICABLE` with `signal=0` and `confidence=0` in every strategy input. No L5 signal enters the short horizon.

## Strategy comparison

The pre-refresh baseline was generated with only L8-001 and L5-001 hard-gated unavailable; weights and all other current JSON files were unchanged. The post-refresh run was produced by the unchanged `gr2 analyze-strategies` command and contains all 15 strategies and four horizons.

| Strategy | Horizon | Pre WGC score | Post WGC score | Delta | Post coverage | Status |
|---|---|---:|---:|---:|---:|---|
| SP-FLOW | 1-5d | +25.0 | +70.0 | +45.0 | 90% | VALID |
| SP-FLOW | 1-3m | -16.0 | -66.0 | -50.0 | 95% | VALID |
| SP-FLOW | 1-3y | +13.0 | +63.0 | +50.0 | 95% | VALID |
| SP-FLOW | 3-10y | -18.0 | -18.0 | +0.0 | 45% | DEGRADED |
| SP-CB | 1-5d | +0.0 | +5.0 | +5.0 | 35% | DEGRADED |
| SP-CB | 1-3m | +0.0 | -65.0 | -65.0 | 95% | VALID |
| SP-CB | 1-3y | +0.0 | +65.0 | +65.0 | 95% | VALID |
| SP-CB | 3-10y | -10.0 | -10.0 | +0.0 | 20% | DEGRADED |
| SP-L0L5 | 1-5d | +30.0 | +35.0 | +5.0 | 55% | DEGRADED |
| SP-L0L5 | 1-3m | +40.0 | +0.0 | -40.0 | 90% | VALID |
| SP-L0L5 | 1-3y | +30.0 | +70.0 | +40.0 | 90% | VALID |
| SP-L0L5 | 3-10y | +0.0 | +0.0 | +0.0 | 10% | DEGRADED |
| SP-ANTI-FIAT | 1-5d | +5.0 | +10.0 | +5.0 | 70% | VALID |
| SP-ANTI-FIAT | 1-3m | +15.0 | -20.0 | -35.0 | 100% | VALID |
| SP-ANTI-FIAT | 1-3y | +45.0 | +80.0 | +35.0 | 100% | VALID |
| SP-ANTI-FIAT | 3-10y | +40.0 | +40.0 | +0.0 | 50% | DEGRADED |

## Interpretation

- L8-001 is active and materially changes SP-FLOW: positive recent ETF flow lifts 1-5d and 1-3y, while the 1-3m calendar comparison is negative. This is a real horizon split, not a strategy-ranking result.
- L5-001 is active for 1-3m and longer horizons. Its negative 1-3m change pulls SP-CB, SP-L0L5, and SP-ANTI-FIAT lower; its positive 1-3y change lifts those strategies.
- L5-001 does not affect any 1-5d score directionally because it is `NOT_APPLICABLE`; low short-horizon coverage in L5-heavy strategies is intentional and remains visible.
- Long-horizon results remain widely `DEGRADED` because the required 756 eligible monthly observations are not available. No degraded result is ranked or presented as a validated forecast.
- Schedule-bound activation is not proof of a true publication timestamp. The JSON and reports preserve that distinction.

## Verification

- `gr2 extract L8-001 -vv` completed with observation `2026-07-31`.
- `gr2 extract L5-001 -vv` completed with observation `2026-07-01`.
- `gr2 analyze-strategies` wrote all 15 current-outlook strategies.
- Step 3 focused WSL suite remains 54 passed.
- No strategy configuration, frozen weight, or non-Tranche-2 variable was changed.

## Disposition

Tranche 2 Step 4 is ready for D/Q review. The next action is owner approval of this comparison; no further tranche should begin until that review is complete.
