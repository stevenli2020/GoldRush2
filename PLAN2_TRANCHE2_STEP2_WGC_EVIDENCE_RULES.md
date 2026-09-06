# Plan 2 Tranche 2 Step 2 — WGC Evidence Rules (Draft)

**Status:** architecture-approved; Step 3 implementation authorized
**Variables:** L8-001 and L5-001
**Scope:** current-outlook only; no weights, backtests, ranking, or Tranche 2 extractor code

## Shared temporal rule

Use calendar month-end `observation_date` for the economic period. `publication_date` remains nullable and is never fabricated. Under the approved conservative release-bound policy, eligibility uses a physically separate `estimated_availability_date` and `availability_source="wgc_schedule_bound_v1"`. `retrieved_at`, HTTP headers, filename dates, and filesystem mtime cannot satisfy either field.

Approved schedule bounds: L8-001 uses month-end + 8 calendar days (T+8); L5-001 uses reference-month end + 11 calendar days (T+11), reflecting the WGC two-month data lag. The JSON must retain `publication_date: null`, `estimated_availability_date`, and `availability_source: "wgc_schedule_bound_v1"`. Before the bound, emit `status="PENDING_RELEASE"`, `signal=0`, `confidence=0`. After the bound, schedule-bound deterministic evidence may use confidence `1.0`, while remaining visibly estimated rather than source-confirmed.

## L8-001 — ETF net flows

- **Measured quantity:** global monthly net flow in physically backed gold ETFs, in tonnes. Do not substitute holdings level or change in flow.
- **Evidence window:** calendar month-end observations, not “last N workbook rows”. Missing months remain missing and do not compress the window.
- **Direction:** positive net flow → `+1`; negative net flow → `-1`; exact zero → `0`.
- **Horizon applicability:** 1-5d and 1-3m require a currently schedule-eligible monthly observation; 1-3y and 3-10y require the approved calendar history and are otherwise degraded.
- **Confidence:** deterministic sign is `1.0` only when the observation is schedule-eligible, current under the variable-specific stale rule, and the required calendar window is complete. Missing month, pending bound, stale evidence, or parse ambiguity → `0.0`.
- **Caveat:** WGC reports both flows and holdings; the extractor must preserve the distinction and never infer flow from holdings without an approved method.

## L5-001 — official-sector purchases

- **Measured quantity:** aggregate monthly net changes in official gold holdings from canonical country rows, in tonnes. This is purchases minus sales, not an absolute holdings level.
- **Evidence window:** calendar month-end observations with late reporters and revisions retained as source facts. Do not use row-count lookbacks or silently fill missing months.
- **Direction:** positive net purchase → `+1`; negative net change → `-1`; exact zero → `0`.
- **Horizon applicability:** 1-5d is formally `NOT_APPLICABLE` with `signal=0`, `confidence=0`; it bypasses release and stale calculations. Monthly data can inform 1-3m, 1-3y, and 3-10y only when the T+11 bound and required calendar history are satisfied.
- **Confidence:** `1.0` only for a schedule-eligible observation, complete required calendar window, and source-confirmed freshness. Pending bound, late-reporter uncertainty, stale data, or insufficient history → `0.0`.
- **Revision rule:** a revised workbook replaces prior observations only with provenance showing the source file and source page; no revision may be hidden by cumulative caching.

## Shared degradation and evidence schema

Each variable JSON should retain `observation_date`, `publication_date: null`, `estimated_availability_date`, `availability_source`, `source_page_date` (provenance only), `retrieved_at`, source URL, workbook identity, and a short evidence summary. Before the estimate, emit `PENDING_RELEASE`; after it, stale/missing-data rules still apply.

## Mandatory Step 3 tests

- One shared WGC collection path with independent L8 flow parsing and L5 net-change parsing; no cross-variable inference or contamination.
- Boundary crossing at T+7 (`PENDING_RELEASE`, confidence `0`) and T+8 (eligible, confidence `1.0`) for L8.
- L5 lag alignment: on 2026-09-06, July 2026 is the latest eligible reference month; August remains pending because month-end + 11 days is 2026-09-11.
- Holdings-shaped input is rejected by the flow parser and degrades rather than being treated as ETF flow.

## Approval questions for D/Q

1. Should both variables remain zero-confidence until WGC exposes explicit publication evidence, or should a separately versioned conservative release-bound policy be approved?
2. Is L5-001 1-5d formally `NOT_APPLICABLE`, or should it remain applicable-but-degraded?
3. Should WGC page/article dates be retained only as provenance, or may they serve as an explicit publication date when the page clearly states the dataset update date?
