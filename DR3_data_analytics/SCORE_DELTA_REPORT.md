# Sparse strategy score delta report

This report compares the owner-recorded initial v1.1 matrix with the current current-outlook run after Plan 1 input gating, soft confidence decay, and the 70% usable-coverage threshold.
It is a current-data diagnostic, not a backtest or a strategy ranking.

Generated from comparison run: `2026-09-06T10:25:37.948714+00:00`.

| Strategy | Horizon | Pre-Audit Score | Post-Audit Score | Delta | Post Coverage | Status | Primary Zeroed Variables |
|---|---|---:|---:|---:|---:|---|---|
| SP-RATE | 1-5d | -60.0 | -45.0 | +15.0 | 85% | VALID | L4-001 (unavailable) |
| SP-RATE | 1-3m | -70.0 | -55.0 | +15.0 | 85% | VALID | L4-001 (unavailable) |
| SP-RATE | 1-3y | -80.0 | -65.0 | +15.0 | 85% | VALID | L4-001 (unavailable) |
| SP-RATE | 3-10y | -60.0 | -45.0 | +15.0 | 75% | VALID | L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-USD | 1-5d | +40.0 | +50.0 | +10.0 | 90% | VALID | L4-001 (unavailable) |
| SP-USD | 1-3m | +30.0 | +40.0 | +10.0 | 90% | VALID | L4-001 (unavailable) |
| SP-USD | 1-3y | -80.0 | -70.0 | +10.0 | 90% | VALID | L4-001 (unavailable) |
| SP-USD | 3-10y | +35.0 | +45.0 | +10.0 | 85% | VALID | L4-001 (unavailable), L8-001 (unavailable) |
| SP-INFL | 1-5d | -50.0 | +10.0 | +60.0 | 40% | DEGRADED | L4-001 (unavailable) |
| SP-INFL | 1-3m | -80.0 | -20.0 | +60.0 | 40% | DEGRADED | L4-001 (unavailable) |
| SP-INFL | 1-3y | -60.0 | +0.0 | +60.0 | 40% | DEGRADED | L4-001 (unavailable) |
| SP-INFL | 3-10y | -60.0 | +0.0 | +60.0 | 20% | DEGRADED | L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-CB | 1-5d | +60.0 | +65.0 | +5.0 | 95% | VALID | L4-001 (unavailable) |
| SP-CB | 1-3m | -70.0 | -65.0 | +5.0 | 95% | VALID | L4-001 (unavailable) |
| SP-CB | 1-3y | +60.0 | +65.0 | +5.0 | 95% | VALID | L4-001 (unavailable) |
| SP-CB | 3-10y | -15.0 | -10.0 | +5.0 | 20% | DEGRADED | L0-002 (unavailable), L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-FLOW | 1-5d | +70.0 | +75.0 | +5.0 | 95% | VALID | L4-001 (unavailable) |
| SP-FLOW | 1-3m | -70.0 | -66.0 | +4.0 | 95% | VALID | L4-001 (unavailable) |
| SP-FLOW | 1-3y | +60.0 | +63.0 | +3.0 | 95% | VALID | L4-001 (unavailable) |
| SP-FLOW | 3-10y | -20.0 | -18.0 | +2.0 | 45% | DEGRADED | L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-TECH | 1-5d | +50.0 | +55.0 | +5.0 | 95% | VALID | L4-001 (unavailable) |
| SP-TECH | 1-3m | +60.0 | +53.0 | -7.0 | 95% | VALID | L4-001 (unavailable) |
| SP-TECH | 1-3y | +30.0 | +11.0 | -19.0 | 95% | VALID | L4-001 (unavailable) |
| SP-TECH | 3-10y | +65.0 | +34.0 | -31.0 | 90% | VALID | L4-001 (unavailable), L8-001 (unavailable) |
| SP-REGIME-PROXY | 1-5d | +10.0 | +10.0 | +0.0 | 30% | DEGRADED | L4-001 (unavailable), L6-001 (stale) |
| SP-REGIME-PROXY | 1-3m | -10.0 | -10.0 | +0.0 | 30% | DEGRADED | L4-001 (unavailable), L6-001 (stale) |
| SP-REGIME-PROXY | 1-3y | -35.0 | +0.0 | +35.0 | 30% | DEGRADED | L4-001 (unavailable), L6-001 (unavailable) |
| SP-REGIME-PROXY | 3-10y | -32.0 | +3.0 | +35.0 | 17% | DEGRADED | L4-001 (unavailable), L5-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-ANTI-FIAT | 1-5d | +40.0 | +40.0 | +0.0 | 100% | VALID | - |
| SP-ANTI-FIAT | 1-3m | -20.0 | -20.0 | +0.0 | 100% | VALID | - |
| SP-ANTI-FIAT | 1-3y | +80.0 | +80.0 | +0.0 | 100% | VALID | - |
| SP-ANTI-FIAT | 3-10y | +40.0 | +40.0 | +0.0 | 50% | DEGRADED | L0-002 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-MACRO | 1-5d | -10.0 | +15.0 | +25.0 | 75% | VALID | L4-001 (unavailable) |
| SP-MACRO | 1-3m | -30.0 | -6.0 | +24.0 | 75% | VALID | L4-001 (unavailable) |
| SP-MACRO | 1-3y | -50.0 | -27.0 | +23.0 | 75% | VALID | L4-001 (unavailable) |
| SP-MACRO | 3-10y | -20.0 | +2.0 | +22.0 | 55% | DEGRADED | L0-002 (unavailable), L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-L0L5 | 1-5d | +60.0 | +70.0 | +10.0 | 90% | VALID | L4-001 (unavailable) |
| SP-L0L5 | 1-3m | -10.0 | +0.0 | +10.0 | 90% | VALID | L4-001 (unavailable) |
| SP-L0L5 | 1-3y | +60.0 | +70.0 | +10.0 | 90% | VALID | L4-001 (unavailable) |
| SP-L0L5 | 3-10y | -10.0 | +0.0 | +10.0 | 10% | DEGRADED | L0-002 (unavailable), L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-L6L7 | 1-5d | +10.0 | -25.0 | -35.0 | 55% | DEGRADED | L4-001 (unavailable), L6-001 (stale) |
| SP-L6L7 | 1-3m | +50.0 | +15.0 | -35.0 | 55% | DEGRADED | L4-001 (unavailable), L6-001 (stale) |
| SP-L6L7 | 1-3y | -40.0 | -35.0 | +5.0 | 55% | DEGRADED | L4-001 (unavailable), L6-001 (unavailable) |
| SP-L6L7 | 3-10y | +15.0 | +20.0 | +5.0 | 50% | DEGRADED | L4-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-SPARSE | 1-5d | +40.0 | +40.0 | +0.0 | 80% | VALID | L4-001 (unavailable), L6-001 (stale) |
| SP-SPARSE | 1-3m | +0.0 | -2.0 | -2.0 | 80% | VALID | L4-001 (unavailable), L6-001 (stale) |
| SP-SPARSE | 1-3y | +10.0 | +16.0 | +6.0 | 80% | VALID | L4-001 (unavailable), L6-001 (unavailable) |
| SP-SPARSE | 3-10y | +0.0 | +4.0 | +4.0 | 50% | DEGRADED | L0-002 (unavailable), L4-001 (unavailable), L5-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-SHORT | 1-5d | +70.0 | +70.0 | +0.0 | 100% | VALID | - |
| SP-SHORT | 1-3m | -20.0 | -17.0 | +3.0 | 95% | VALID | L4-001 (unavailable) |
| SP-SHORT | 1-3y | +5.0 | +15.0 | +10.0 | 85% | VALID | L4-001 (unavailable), L6-001 (unavailable) |
| SP-SHORT | 3-10y | -40.0 | -20.0 | +20.0 | 40% | DEGRADED | L0-002 (unavailable), L4-001 (unavailable), L5-001 (unavailable), L6-001 (unavailable), L8-001 (unavailable) |
| SP-LONG | 1-5d | +60.0 | +60.0 | +0.0 | 90% | VALID | L4-001 (unavailable), L6-001 (stale) |
| SP-LONG | 1-3m | -20.0 | -12.0 | +8.0 | 80% | VALID | L4-001 (unavailable), L6-001 (stale) |
| SP-LONG | 1-3y | -10.0 | +15.0 | +25.0 | 75% | VALID | L4-001 (unavailable) |
| SP-LONG | 3-10y | -40.0 | -15.0 | +25.0 | 25% | DEGRADED | L0-002 (unavailable), L4-001 (unavailable), L5-001 (unavailable), L8-001 (unavailable) |
| SP-ALL | 1-5d | +2.2 | +1.3 | -0.9 | 89% | VALID | L3-002 (unavailable), L3-003 (unavailable), L3-006 (unavailable), L4-001 (unavailable), L6-001 (stale) |
| SP-ALL | 1-3m | +2.2 | +0.9 | -1.3 | 89% | VALID | L3-002 (unavailable), L3-003 (unavailable), L3-006 (unavailable), L4-001 (unavailable), L6-001 (stale) |
| SP-ALL | 1-3y | +2.2 | +4.4 | +2.2 | 84% | VALID | L3-002 (unavailable), L3-003 (unavailable), L3-005 (invalid), L3-006 (unavailable), L4-001 (unavailable), L6-001 (unavailable), L6-002 (unavailable) |
| SP-ALL | 3-10y | -8.9 | -5.3 | +3.6 | 64% | DEGRADED | L0-002 (unavailable), L0-003 (unavailable), L0-009 (unavailable), L3-002 (unavailable), L3-003 (unavailable), L3-004 (unavailable), L3-005 (invalid), L3-006 (unavailable), L4-001 (unavailable), L4-009 (unavailable), L5-001 (unavailable), L5-002 (unavailable), L5-006 (unavailable), L6-001 (unavailable), L6-002 (unavailable), L8-001 (unavailable) |

21 of 60 strategy-horizon results are DEGRADED under the 70% threshold.
A zeroed variable is excluded because the current run marks it stale, unavailable, invalid, missing, or inapplicable; it does not mean the underlying economic force is zero.
