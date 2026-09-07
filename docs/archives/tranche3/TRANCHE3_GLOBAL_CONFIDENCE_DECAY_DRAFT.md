# Tranche 3 Global Confidence Decay Rule Draft

**Status:** proposed; D/Q approval required

## Decision

The frequency-to-horizon decay is **not yet universal**. The current `0.7` for L6-001 is a V1, variable-specific provisional policy because its 1–3m signal is an extension of a daily geopolitical-risk pulse, not a directly observed 1–3m series. It must not silently be applied to L1-001 or other daily/weekly variables.

Universal cross-variable comparability requires a separate approved matrix and calibration study. Until then, each extractor must declare its confidence policy explicitly; deterministic source validity remains distinct from predictive correctness.

## Candidate universal matrix for review

This is a proposal, not an active rule:

| Source frequency | 1-5d | 1-3m | 1-3y | 3-10y |
|---|---:|---:|---:|---:|
| Daily | 1.0 | 0.7 | N/A | N/A |
| Weekly | 0.8 | 0.7 | N/A | N/A |
| Monthly | N/A or source-specific | 1.0 | 0.8 | 0.7 |

The matrix cannot be adopted by inference. D/Q must approve whether the numbers represent evidence quality, forecast reliability, or another defined quantity, and must require out-of-sample validation before using them for cross-strategy comparison.
