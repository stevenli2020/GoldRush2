# Plan 2 Step 4 — L4-001 Controlled Refresh Comparison

This report compares the frozen strategy run captured immediately before the L4-001 refresh with the unchanged strategy engine after the P0-corrected L4-001 input. The prior completion matrix is superseded.
The comparison is current-outlook evidence, not a backtest or a strategy ranking.

L4-001 uses publication-aligned `CPI_YoY_12m_MA`; the refreshed smoothed rate is unavailable, signal `0`, confidence `0`. The refresh used live FRED data; its latest eligible smoothed observation is dated None with publication date None.

| Strategy | Horizon | Pre Score | Post Score | Delta | L4 Pre Contribution | L4 Post Contribution | Post Coverage | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| SP-RATE | 1-5d | -60.00 | -45.00 | +15.00 | -15.00 | +0.00 | 85% | VALID |
| SP-RATE | 1-3m | -70.00 | -55.00 | +15.00 | -15.00 | +0.00 | 85% | VALID |
| SP-RATE | 1-3y | -80.00 | -65.00 | +15.00 | -15.00 | +0.00 | 85% | VALID |
| SP-RATE | 3-10y | -60.00 | -45.00 | +15.00 | -15.00 | +0.00 | 75% | VALID |
| SP-USD | 1-5d | +40.00 | +50.00 | +10.00 | -10.00 | +0.00 | 90% | VALID |
| SP-USD | 1-3m | +30.00 | +40.00 | +10.00 | -10.00 | +0.00 | 90% | VALID |
| SP-USD | 1-3y | -80.00 | -70.00 | +10.00 | -10.00 | +0.00 | 90% | VALID |
| SP-USD | 3-10y | +35.00 | +45.00 | +10.00 | -10.00 | +0.00 | 85% | VALID |
| SP-INFL | 1-5d | -50.00 | +10.00 | +60.00 | -60.00 | +0.00 | 40% | DEGRADED |
| SP-INFL | 1-3m | -80.00 | -20.00 | +60.00 | -60.00 | +0.00 | 40% | DEGRADED |
| SP-INFL | 1-3y | -60.00 | +0.00 | +60.00 | -60.00 | +0.00 | 40% | DEGRADED |
| SP-INFL | 3-10y | -60.00 | +0.00 | +60.00 | -60.00 | +0.00 | 20% | DEGRADED |
| SP-CB | 1-5d | +60.00 | +65.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-CB | 1-3m | -70.00 | -65.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-CB | 1-3y | +60.00 | +65.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-CB | 3-10y | -15.00 | -10.00 | +5.00 | -5.00 | +0.00 | 20% | DEGRADED |
| SP-FLOW | 1-5d | +70.00 | +75.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-FLOW | 1-3m | -71.00 | -66.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-FLOW | 1-3y | +58.00 | +63.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-FLOW | 3-10y | -23.00 | -18.00 | +5.00 | -5.00 | +0.00 | 45% | DEGRADED |
| SP-TECH | 1-5d | +50.00 | +55.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-TECH | 1-3m | +48.00 | +53.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-TECH | 1-3y | +6.00 | +11.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-TECH | 3-10y | +29.00 | +34.00 | +5.00 | -5.00 | +0.00 | 90% | VALID |
| SP-REGIME-PROXY | 1-5d | -25.00 | +10.00 | +35.00 | -35.00 | +0.00 | 30% | DEGRADED |
| SP-REGIME-PROXY | 1-3m | -45.00 | -10.00 | +35.00 | -35.00 | +0.00 | 30% | DEGRADED |
| SP-REGIME-PROXY | 1-3y | -35.00 | +0.00 | +35.00 | -35.00 | +0.00 | 30% | DEGRADED |
| SP-REGIME-PROXY | 3-10y | -32.00 | +3.00 | +35.00 | -35.00 | +0.00 | 17% | DEGRADED |
| SP-ANTI-FIAT | 1-5d | +40.00 | +40.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-ANTI-FIAT | 1-3m | -20.00 | -20.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-ANTI-FIAT | 1-3y | +80.00 | +80.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-ANTI-FIAT | 3-10y | +40.00 | +40.00 | +0.00 | +0.00 | +0.00 | 50% | DEGRADED |
| SP-MACRO | 1-5d | -10.00 | +15.00 | +25.00 | -25.00 | +0.00 | 75% | VALID |
| SP-MACRO | 1-3m | -31.00 | -6.00 | +25.00 | -25.00 | +0.00 | 75% | VALID |
| SP-MACRO | 1-3y | -52.00 | -27.00 | +25.00 | -25.00 | +0.00 | 75% | VALID |
| SP-MACRO | 3-10y | -23.00 | +2.00 | +25.00 | -25.00 | +0.00 | 55% | DEGRADED |
| SP-L0L5 | 1-5d | +60.00 | +70.00 | +10.00 | -10.00 | +0.00 | 90% | VALID |
| SP-L0L5 | 1-3m | -10.00 | +0.00 | +10.00 | -10.00 | +0.00 | 90% | VALID |
| SP-L0L5 | 1-3y | +60.00 | +70.00 | +10.00 | -10.00 | +0.00 | 90% | VALID |
| SP-L0L5 | 3-10y | -10.00 | +0.00 | +10.00 | -10.00 | +0.00 | 10% | DEGRADED |
| SP-L6L7 | 1-5d | -30.00 | -25.00 | +5.00 | -5.00 | +0.00 | 55% | DEGRADED |
| SP-L6L7 | 1-3m | +10.00 | +15.00 | +5.00 | -5.00 | +0.00 | 55% | DEGRADED |
| SP-L6L7 | 1-3y | -40.00 | -35.00 | +5.00 | -5.00 | +0.00 | 55% | DEGRADED |
| SP-L6L7 | 3-10y | +15.00 | +20.00 | +5.00 | -5.00 | +0.00 | 50% | DEGRADED |
| SP-SPARSE | 1-5d | +30.00 | +40.00 | +10.00 | -10.00 | +0.00 | 80% | VALID |
| SP-SPARSE | 1-3m | -12.00 | -2.00 | +10.00 | -10.00 | +0.00 | 80% | VALID |
| SP-SPARSE | 1-3y | +6.00 | +16.00 | +10.00 | -10.00 | +0.00 | 80% | VALID |
| SP-SPARSE | 3-10y | -6.00 | +4.00 | +10.00 | -10.00 | +0.00 | 50% | DEGRADED |
| SP-SHORT | 1-5d | +70.00 | +70.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-SHORT | 1-3m | -22.00 | -17.00 | +5.00 | -5.00 | +0.00 | 95% | VALID |
| SP-SHORT | 1-3y | +5.00 | +15.00 | +10.00 | -10.00 | +0.00 | 85% | VALID |
| SP-SHORT | 3-10y | -40.00 | -20.00 | +20.00 | -20.00 | +0.00 | 40% | DEGRADED |
| SP-LONG | 1-5d | +55.00 | +60.00 | +5.00 | -5.00 | +0.00 | 90% | VALID |
| SP-LONG | 1-3m | -27.00 | -12.00 | +15.00 | -15.00 | +0.00 | 80% | VALID |
| SP-LONG | 1-3y | -10.00 | +15.00 | +25.00 | -25.00 | +0.00 | 75% | VALID |
| SP-LONG | 3-10y | -40.00 | -15.00 | +25.00 | -25.00 | +0.00 | 25% | DEGRADED |
| SP-ALL | 1-5d | -0.89 | +1.33 | +2.22 | -2.22 | +0.00 | 89% | VALID |
| SP-ALL | 1-3m | -1.33 | +0.89 | +2.22 | -2.22 | +0.00 | 89% | VALID |
| SP-ALL | 1-3y | +2.22 | +4.44 | +2.22 | -2.22 | +0.00 | 84% | VALID |
| SP-ALL | 3-10y | -7.56 | -5.33 | +2.22 | -2.22 | +0.00 | 64% | DEGRADED |

## Interpretation

- FRED `realtime_start` is vintage metadata, not a publication date. When no explicit publication date is available, the extractor conservatively produces zero-confidence output rather than treating the vintage date as release evidence.
- The strategy configurations and horizon weights were not changed. Any L4-001 score delta is therefore attributable to the corrected input gate; no stale CPI contribution is allowed through.
- `DEGRADED` statuses remain data-coverage warnings; they are not converted into rankings or suppressed scores.

## Next correction tranche (blocked)

Do not proceed to Tranche 2 yet. L8-001 ETF flows and L5-001 official-sector purchases remain the proposed next tranche, but require owner approval of this P0 correction and their publication-date contracts first.
