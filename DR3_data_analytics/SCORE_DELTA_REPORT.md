# Sparse strategy score delta report

This report compares the owner-recorded initial v1.1 matrix with the current current-outlook run after Plan 1 input gating, soft confidence decay, and the 70% usable-coverage threshold.
It is a current-data diagnostic, not a backtest or a strategy ranking.

Generated from comparison run: `2026-09-06T09:28:17.456656+00:00`.

| Strategy | Horizon | Pre-Audit Score | Post-Audit Score | Delta | Post Coverage | Status | Primary Zeroed Variables |
|---|---|---:|---:|---:|---:|---|---|
| SP-RATE | 1-5d | -60.0 | -37.5 | +22.5 | 100% | VALID | - |
| SP-RATE | 1-3m | -70.0 | -47.5 | +22.5 | 100% | VALID | - |
| SP-RATE | 1-3y | -80.0 | -57.5 | +22.5 | 100% | VALID | - |
| SP-RATE | 3-10y | -60.0 | -37.5 | +22.5 | 90% | VALID | L5-001 (unavailable), L8-001 (unavailable) |
| SP-USD | 1-5d | +40.0 | +55.0 | +15.0 | 100% | VALID | - |
| SP-USD | 1-3m | +30.0 | +45.0 | +15.0 | 100% | VALID | - |
| SP-USD | 1-3y | -80.0 | -65.0 | +15.0 | 100% | VALID | - |
| SP-USD | 3-10y | +35.0 | +50.0 | +15.0 | 95% | VALID | L8-001 (unavailable) |
| SP-INFL | 1-5d | -50.0 | +40.0 | +90.0 | 100% | VALID | - |
| SP-INFL | 1-3m | -80.0 | +10.0 | +90.0 | 100% | VALID | - |
| SP-INFL | 1-3y | -60.0 | +30.0 | +90.0 | 100% | VALID | - |
| SP-INFL | 3-10y | -60.0 | +30.0 | +90.0 | 80% | VALID | L5-001 (unavailable), L8-001 (unavailable) |
| SP-CB | 1-5d | +60.0 | +67.5 | +7.5 | 100% | VALID | - |
| SP-CB | 1-3m | -70.0 | -62.5 | +7.5 | 100% | VALID | - |
| SP-CB | 1-3y | +60.0 | +67.5 | +7.5 | 100% | VALID | - |
| SP-CB | 3-10y | -15.0 | -7.5 | +7.5 | 25% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-FLOW | 1-5d | +70.0 | +77.5 | +7.5 | 100% | VALID | - |
| SP-FLOW | 1-3m | -70.0 | -63.5 | +6.5 | 100% | VALID | - |
| SP-FLOW | 1-3y | +60.0 | +65.5 | +5.5 | 100% | VALID | - |
| SP-FLOW | 3-10y | -20.0 | -15.5 | +4.5 | 50% | DEGRADED | L5-001 (unavailable), L8-001 (unavailable) |
| SP-TECH | 1-5d | +50.0 | +57.5 | +7.5 | 100% | VALID | - |
| SP-TECH | 1-3m | +60.0 | +55.5 | -4.5 | 100% | VALID | - |
| SP-TECH | 1-3y | +30.0 | +13.5 | -16.5 | 100% | VALID | - |
| SP-TECH | 3-10y | +65.0 | +36.5 | -28.5 | 95% | VALID | L8-001 (unavailable) |
| SP-REGIME-PROXY | 1-5d | +10.0 | +27.5 | +17.5 | 65% | DEGRADED | L6-001 (stale) |
| SP-REGIME-PROXY | 1-3m | -10.0 | +7.5 | +17.5 | 65% | DEGRADED | L6-001 (stale) |
| SP-REGIME-PROXY | 1-3y | -35.0 | +17.5 | +52.5 | 65% | DEGRADED | L6-001 (unavailable) |
| SP-REGIME-PROXY | 3-10y | -32.0 | +20.5 | +52.5 | 52% | DEGRADED | L5-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-ANTI-FIAT | 1-5d | +40.0 | +40.0 | +0.0 | 100% | VALID | - |
| SP-ANTI-FIAT | 1-3m | -20.0 | -20.0 | +0.0 | 100% | VALID | - |
| SP-ANTI-FIAT | 1-3y | +80.0 | +80.0 | +0.0 | 100% | VALID | - |
| SP-ANTI-FIAT | 3-10y | +40.0 | +40.0 | +0.0 | 50% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-MACRO | 1-5d | -10.0 | +27.5 | +37.5 | 100% | VALID | - |
| SP-MACRO | 1-3m | -30.0 | +6.5 | +36.5 | 100% | VALID | - |
| SP-MACRO | 1-3y | -50.0 | -14.5 | +35.5 | 100% | VALID | - |
| SP-MACRO | 3-10y | -20.0 | +14.5 | +34.5 | 80% | VALID | L0-002 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-L0L5 | 1-5d | +60.0 | +75.0 | +15.0 | 100% | VALID | - |
| SP-L0L5 | 1-3m | -10.0 | +5.0 | +15.0 | 100% | VALID | - |
| SP-L0L5 | 1-3y | +60.0 | +75.0 | +15.0 | 100% | VALID | - |
| SP-L0L5 | 3-10y | -10.0 | +5.0 | +15.0 | 20% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-L6L7 | 1-5d | +10.0 | -22.5 | -32.5 | 60% | DEGRADED | L6-001 (stale) |
| SP-L6L7 | 1-3m | +50.0 | +17.5 | -32.5 | 60% | DEGRADED | L6-001 (stale) |
| SP-L6L7 | 1-3y | -40.0 | -32.5 | +7.5 | 60% | DEGRADED | L6-001 (unavailable) |
| SP-L6L7 | 3-10y | +15.0 | +22.5 | +7.5 | 55% | DEGRADED | L6-001 (unavailable), L8-001 (unavailable) |
| SP-SPARSE | 1-5d | +40.0 | +45.0 | +5.0 | 90% | VALID | L6-001 (stale) |
| SP-SPARSE | 1-3m | +0.0 | +3.0 | +3.0 | 90% | VALID | L6-001 (stale) |
| SP-SPARSE | 1-3y | +10.0 | +21.0 | +11.0 | 90% | VALID | L6-001 (unavailable) |
| SP-SPARSE | 3-10y | +0.0 | +9.0 | +9.0 | 60% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-SHORT | 1-5d | +70.0 | +70.0 | +0.0 | 100% | VALID | - |
| SP-SHORT | 1-3m | -20.0 | -14.5 | +5.5 | 100% | VALID | - |
| SP-SHORT | 1-3y | +5.0 | +20.0 | +15.0 | 95% | VALID | L6-001 (unavailable) |
| SP-SHORT | 3-10y | -40.0 | -10.0 | +30.0 | 60% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-LONG | 1-5d | +60.0 | +62.5 | +2.5 | 95% | VALID | L6-001 (stale) |
| SP-LONG | 1-3m | -20.0 | -4.5 | +15.5 | 95% | VALID | L6-001 (stale) |
| SP-LONG | 1-3y | -10.0 | +27.5 | +37.5 | 100% | VALID | - |
| SP-LONG | 3-10y | -40.0 | -2.5 | +37.5 | 50% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-ALL | 1-5d | +2.2 | +2.4 | +0.2 | 91% | VALID | L3-002 (unavailable), L3-003 (unavailable), L3-006 (unavailable), L6-001 (stale) |
| SP-ALL | 1-3m | +2.2 | +2.0 | -0.2 | 91% | VALID | L3-002 (unavailable), L3-003 (unavailable), L3-006 (unavailable), L6-001 (stale) |
| SP-ALL | 1-3y | +2.2 | +5.6 | +3.4 | 87% | VALID | L3-002 (unavailable), L3-003 (unavailable), L3-005 (invalid), L3-006 (unavailable), L6-001 (unavailable), L6-002 (unavailable) |
| SP-ALL | 3-10y | -8.9 | -4.2 | +4.7 | 67% | DEGRADED | L0-002 (unavailable), L0-003 (unavailable), L0-009 (unavailable), L3-002 (unavailable), L3-003 (unavailable), L3-004 (unavailable), L3-005 (invalid), L3-006 (unavailable), L4-009 (unavailable), L5-001 (unavailable), L5-002 (unavailable), L5-006 (unavailable), L6-001 (unavailable), L6-002 (unavailable), L8-001 (unavailable) |

16 of 60 strategy-horizon results are DEGRADED under the 70% threshold.
A zeroed variable is excluded because the current run marks it stale, unavailable, invalid, missing, or inapplicable; it does not mean the underlying economic force is zero.
