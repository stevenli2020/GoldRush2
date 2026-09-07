# Plan 2 Step 4 — P0 FRED Metadata and Stale-Gating Bug Report

**Status:** fixed and verified; Plan 2 archived by owner/Q approval; Tranche 2 Step 1 authorized.

## Finding

The prior L4-001 output reported observation period `2025-09-01`, publication date `2026-08-12`, and confidence `1.0`. The `2026-08-12` value came from FRED's `realtime_start` field. That field identifies a vintage/realtime window, not the economic release date, so it could not be used as publication evidence or freshness metadata.

The stale check also compared the decision date with that incorrectly mapped publication date. Consequently, a stale smoothed observation could pass the 62-day gate and contribute to DR3 with full confidence.

## Correction

- FRED parsing now stores `realtime_start` only as `vintage_date` and accepts `publication_date` only when explicitly supplied by the source payload.
- L4-001 freshness is now calculated from the latest smoothed evidence observation period (`current["date"]`) against the decision date.
- A stale or publication-unaligned L4-001 input emits `signal=0`, `confidence=0`, and an explicit `STALE DATA` or `INSUFFICIENT HISTORY` explanation.
- DR3 strategy weights and aggregation remain unchanged; zero-confidence L4-001 inputs are hard-gated and are not renormalized into other variables.

## Verification

- Regression suite: `16 passed` for L4-001, including the exact failure case where observation date is `2025-09-01` and vintage date is `2026-08-12`.
- Controlled live extraction on 2026-09-06: FRED was reachable, but no explicit publication dates were present in the observations; L4-001 therefore produced zero-confidence `INSUFFICIENT HISTORY` output rather than a fabricated fresh signal.
- `gr2 analyze-strategies` was rerun with the corrected L4-001 JSON.
- The updated comparison and score-delta reports contain the post-fix matrix and coverage/status fields.

## Disposition

The earlier Plan 2 Step 4 completion record was superseded during the incident review. After approval of this correction, Plan 2 Step 4 is closed. Tranche 2 may proceed only through the authorized Step 1/Step 2 contract drafts; no L8/L5 extractor implementation is authorized yet.
