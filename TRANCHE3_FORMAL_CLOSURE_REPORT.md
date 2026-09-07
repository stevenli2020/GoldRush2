# Tranche 3 Formal Closure Report

## Validation

- CLI now rejects both missing and mismatched `window_config` declarations when the output frequency has an approved rule.
- L4-006 is active under the approved rule: deficit/GDP falls → `+1`; rises → `-1`.
- Fresh L4-006 output contains `window_config: v1.1_quarterly_12_40` and valid horizons have confidence `1.0`.
- Full WSL suite: **840 passed, 2 deselected, 991 warnings**.

## Final strategy matrix

| Strategy | 1-5d | 1-3m | 1-3y | 3-10y |
|---|---:|---:|---:|---:|
| SP-RATE | -50.0 | -55.0 | -75.0 | -45.0 |
| SP-USD | 50.0 | 40.0 | -70.0 | 40.0 |
| SP-INFL | -5.0 | -20.0 | -30.0 | 10.0 |
| SP-CB | 5.0 | -65.0 | -55.0 | 55.0 |
| SP-FLOW | 70.0 | -66.0 | 53.0 | -58.0 |
| SP-TECH | 55.0 | 53.0 | 11.0 | 29.0 |
| SP-REGIME-PROXY | 35.0 | 14.5 | -20.0 | 10.0 |
| SP-ANTI-FIAT | 10.0 | -20.0 | 20.0 | 80.0 |
| SP-MACRO | 5.0 | -6.0 | -47.0 | 12.0 |
| SP-L0L5 | 35.0 | 0.0 | 0.0 | 70.0 |
| SP-L6L7 | 15.0 | 43.0 | -35.0 | 15.0 |
| SP-SPARSE | 40.0 | 5.0 | -4.0 | 14.0 |
| SP-SHORT | 70.0 | -17.0 | -5.0 | -5.0 |
| SP-LONG | 65.0 | -8.5 | -25.0 | 25.0 |
| SP-ALL | 1.333333 | 2.444445 | -4.444444 | 7.999999 |

SP-ANTI-FIAT `3-10y` includes L4-006's approved `+1` signal at weight `0.40`, contributing `+40.0` to the raw weighted score. The final score is `80.0`.

## Closure statement

The CLI None escape is closed, L4-006 is active under its approved directional evidence rule, and the final matrix was regenerated only after the zero-failure test run. No discussion or implementation of future phases is included in this report.
