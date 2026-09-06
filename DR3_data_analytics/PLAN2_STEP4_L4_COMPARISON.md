# Plan 2 Step 4 — L4-001 Controlled Refresh Comparison

This report compares the frozen strategy run captured immediately before the L4-001 refresh with the unchanged strategy engine after the refresh.
The comparison is current-outlook evidence, not a backtest or a strategy ranking.

L4-001 now uses publication-aligned `CPI_YoY_12m_MA` and emits `+0.5` for the refreshed 2.70% smoothed rate. The refreshed source was unavailable, so the extractor used a cached observation published 2026-08-12; the cache remained within the 62-day L4 freshness limit on the 2026-09-06 run.

| Strategy | Horizon | Pre Score | Post Score | Delta | L4 Pre Contribution | L4 Post Contribution | Post Coverage | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| SP-RATE | 1-5d | -60.00 | -37.50 | +22.50 | -15.00 | +7.50 | 100% | VALID |
| SP-RATE | 1-3m | -70.00 | -47.50 | +22.50 | -15.00 | +7.50 | 100% | VALID |
| SP-RATE | 1-3y | -80.00 | -57.50 | +22.50 | -15.00 | +7.50 | 100% | VALID |
| SP-RATE | 3-10y | -60.00 | -37.50 | +22.50 | -15.00 | +7.50 | 90% | VALID |
| SP-USD | 1-5d | +40.00 | +55.00 | +15.00 | -10.00 | +5.00 | 100% | VALID |
| SP-USD | 1-3m | +30.00 | +45.00 | +15.00 | -10.00 | +5.00 | 100% | VALID |
| SP-USD | 1-3y | -80.00 | -65.00 | +15.00 | -10.00 | +5.00 | 100% | VALID |
| SP-USD | 3-10y | +35.00 | +50.00 | +15.00 | -10.00 | +5.00 | 95% | VALID |
| SP-INFL | 1-5d | -50.00 | +40.00 | +90.00 | -60.00 | +30.00 | 100% | VALID |
| SP-INFL | 1-3m | -80.00 | +10.00 | +90.00 | -60.00 | +30.00 | 100% | VALID |
| SP-INFL | 1-3y | -60.00 | +30.00 | +90.00 | -60.00 | +30.00 | 100% | VALID |
| SP-INFL | 3-10y | -60.00 | +30.00 | +90.00 | -60.00 | +30.00 | 80% | VALID |
| SP-CB | 1-5d | +60.00 | +67.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-CB | 1-3m | -70.00 | -62.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-CB | 1-3y | +60.00 | +67.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-CB | 3-10y | -15.00 | -7.50 | +7.50 | -5.00 | +2.50 | 25% | DEGRADED |
| SP-FLOW | 1-5d | +70.00 | +77.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-FLOW | 1-3m | -71.00 | -63.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-FLOW | 1-3y | +58.00 | +65.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-FLOW | 3-10y | -23.00 | -15.50 | +7.50 | -5.00 | +2.50 | 50% | DEGRADED |
| SP-TECH | 1-5d | +50.00 | +57.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-TECH | 1-3m | +48.00 | +55.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-TECH | 1-3y | +6.00 | +13.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-TECH | 3-10y | +29.00 | +36.50 | +7.50 | -5.00 | +2.50 | 95% | VALID |
| SP-REGIME-PROXY | 1-5d | -25.00 | +27.50 | +52.50 | -35.00 | +17.50 | 65% | DEGRADED |
| SP-REGIME-PROXY | 1-3m | -45.00 | +7.50 | +52.50 | -35.00 | +17.50 | 65% | DEGRADED |
| SP-REGIME-PROXY | 1-3y | -35.00 | +17.50 | +52.50 | -35.00 | +17.50 | 65% | DEGRADED |
| SP-REGIME-PROXY | 3-10y | -32.00 | +20.50 | +52.50 | -35.00 | +17.50 | 52% | DEGRADED |
| SP-ANTI-FIAT | 1-5d | +40.00 | +40.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-ANTI-FIAT | 1-3m | -20.00 | -20.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-ANTI-FIAT | 1-3y | +80.00 | +80.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-ANTI-FIAT | 3-10y | +40.00 | +40.00 | +0.00 | +0.00 | +0.00 | 50% | DEGRADED |
| SP-MACRO | 1-5d | -10.00 | +27.50 | +37.50 | -25.00 | +12.50 | 100% | VALID |
| SP-MACRO | 1-3m | -31.00 | +6.50 | +37.50 | -25.00 | +12.50 | 100% | VALID |
| SP-MACRO | 1-3y | -52.00 | -14.50 | +37.50 | -25.00 | +12.50 | 100% | VALID |
| SP-MACRO | 3-10y | -23.00 | +14.50 | +37.50 | -25.00 | +12.50 | 80% | VALID |
| SP-L0L5 | 1-5d | +60.00 | +75.00 | +15.00 | -10.00 | +5.00 | 100% | VALID |
| SP-L0L5 | 1-3m | -10.00 | +5.00 | +15.00 | -10.00 | +5.00 | 100% | VALID |
| SP-L0L5 | 1-3y | +60.00 | +75.00 | +15.00 | -10.00 | +5.00 | 100% | VALID |
| SP-L0L5 | 3-10y | -10.00 | +5.00 | +15.00 | -10.00 | +5.00 | 20% | DEGRADED |
| SP-L6L7 | 1-5d | -30.00 | -22.50 | +7.50 | -5.00 | +2.50 | 60% | DEGRADED |
| SP-L6L7 | 1-3m | +10.00 | +17.50 | +7.50 | -5.00 | +2.50 | 60% | DEGRADED |
| SP-L6L7 | 1-3y | -40.00 | -32.50 | +7.50 | -5.00 | +2.50 | 60% | DEGRADED |
| SP-L6L7 | 3-10y | +15.00 | +22.50 | +7.50 | -5.00 | +2.50 | 55% | DEGRADED |
| SP-SPARSE | 1-5d | +30.00 | +45.00 | +15.00 | -10.00 | +5.00 | 90% | VALID |
| SP-SPARSE | 1-3m | -12.00 | +3.00 | +15.00 | -10.00 | +5.00 | 90% | VALID |
| SP-SPARSE | 1-3y | +6.00 | +21.00 | +15.00 | -10.00 | +5.00 | 90% | VALID |
| SP-SPARSE | 3-10y | -6.00 | +9.00 | +15.00 | -10.00 | +5.00 | 60% | DEGRADED |
| SP-SHORT | 1-5d | +70.00 | +70.00 | +0.00 | +0.00 | +0.00 | 100% | VALID |
| SP-SHORT | 1-3m | -22.00 | -14.50 | +7.50 | -5.00 | +2.50 | 100% | VALID |
| SP-SHORT | 1-3y | +5.00 | +20.00 | +15.00 | -10.00 | +5.00 | 95% | VALID |
| SP-SHORT | 3-10y | -40.00 | -10.00 | +30.00 | -20.00 | +10.00 | 60% | DEGRADED |
| SP-LONG | 1-5d | +55.00 | +62.50 | +7.50 | -5.00 | +2.50 | 95% | VALID |
| SP-LONG | 1-3m | -27.00 | -4.50 | +22.50 | -15.00 | +7.50 | 95% | VALID |
| SP-LONG | 1-3y | -10.00 | +27.50 | +37.50 | -25.00 | +12.50 | 100% | VALID |
| SP-LONG | 3-10y | -40.00 | -2.50 | +37.50 | -25.00 | +12.50 | 50% | DEGRADED |
| SP-ALL | 1-5d | -0.89 | +2.44 | +3.33 | -2.22 | +1.11 | 91% | VALID |
| SP-ALL | 1-3m | -1.33 | +2.00 | +3.33 | -2.22 | +1.11 | 91% | VALID |
| SP-ALL | 1-3y | +2.22 | +5.56 | +3.33 | -2.22 | +1.11 | 87% | VALID |
| SP-ALL | 3-10y | -7.56 | -4.22 | +3.33 | -2.22 | +1.11 | 67% | DEGRADED |

## Interpretation

- The L4-001 contribution changes from the old CPI index-direction output to the approved smoothed rate output. Because the refreshed `CPI_YoY_12m_MA` is 2.70%, L4-001 contributes a positive half-strength signal wherever its strategy weight is present.
- The strategy configurations and horizon weights were not changed. Score deltas therefore arise from the L4-001 refresh and the explicit acceptance of the approved half-strength signal.
- `DEGRADED` statuses remain data-coverage warnings; they are not converted into rankings or suppressed scores.

## Next correction tranche

Proceed to the shared monthly WGC tranche: L8-001 ETF flows and L5-001 official-sector purchases. Their current extractors reuse row-count lookbacks across monthly data, and both require publication-date contracts, calendar-aligned windows, and separate flow-versus-change semantics before implementation.
