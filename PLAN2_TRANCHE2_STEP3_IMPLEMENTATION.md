# Plan 2 Tranche 2 Step 3 — WGC Extractor Implementation

**Status:** implemented; review required
**Scope:** L8-001 ETF flows and L5-001 official-sector purchases only

## Implemented

- Added versioned `wgc_schedule_bound_v1` availability calculations while keeping `publication_date` null.
- L8-001 uses month-end + 8 calendar days (T+8).
- L5-001 uses reference-month end + 11 calendar days (T+11), so on 2026-09-06 July 2026 is eligible and August remains pending until 2026-09-11.
- Added `estimated_availability_date`, `availability_source`, `source_page_date`, and `retrieved_at` fields. Page dates remain provenance only.
- Added `PENDING_RELEASE` hard gating with signal/confidence zero.
- Marked L5-001 1-5d as `NOT_APPLICABLE` with signal/confidence zero.
- Kept flow and official-change parsing independent while reusing the shared WGC collector module.
- Holdings-shaped workbooks are rejected by the ETF flow parser.

## Verification

- L8/L5/collector/WGC focused suite: **54 passed** under WSL.
- Covered T+7/T+8 boundary crossing, L5 July-vs-August lag alignment, shared parser isolation, and holdings/flows separation.
- No live WGC refresh or strategy matrix regeneration was performed in Step 3.

## Review boundary

Step 4 must perform a controlled WGC refresh, inspect source/cache status, regenerate only L8/L5 current JSON, rerun unchanged strategies, and explain score deltas. It must not alter frozen weights or infer a true publication date from the schedule bound.
