# Tranche 3 Confidence Decay Rule Proposal

**Status:** proposed; D/Q approval required before further confidence-policy changes

## Problem

L6-001 currently assigns `1-5d = 1.0` and `1-3m = 0.7`. The `0.7` value is not an empirical probability and has no validated economic calibration. It is a provisional policy constant inherited from the earlier extractor contract.

## V1 proposal

Until a walk-forward calibration is approved, confidence values are interpreted as bounded evidence-quality weights, not probabilities of correctness:

| Source frequency | Horizon | Confidence | Rationale |
|---|---|---:|---|
| Daily GPRD_ACT | 1-5d | 1.0 | Direct alignment with the daily signal construction. |
| Daily GPRD_ACT | 1-3m | 0.7 | Provisional decay for horizon extension; not a statistical claim. |
| Daily GPRD_ACT | 1-3y | 0.0 | `NOT_APPLICABLE`. |
| Daily GPRD_ACT | 3-10y | 0.0 | `NOT_APPLICABLE`. |

The value `0.7` must not be described as calibrated confidence. It is a frozen V1 policy parameter pending D/Q approval. Any future replacement must be a new rule version with an out-of-sample calibration report, not an in-place tweak.

## Implementation control

The extractor's confidence map must be declared in a named constant block (or versioned configuration) with a reference to this proposal. Zero-confidence gating remains absolute, and no missing-data weight is renormalized.
