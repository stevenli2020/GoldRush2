# Plan 2 Tranche 2 Step 2 — WGC Evidence Rules (Draft)

**Status:** draft for D/Q approval; implementation is not authorized by this document
**Variables:** L8-001 and L5-001
**Scope:** current-outlook only; no weights, backtests, ranking, or Tranche 2 extractor code

## Shared temporal rule

Use calendar month-end `observation_date` for the economic period and an explicit source `publication_date` for availability. An observation is eligible only when `publication_date <= decision_date`. `retrieved_at`, HTTP headers, filename dates, and filesystem mtime cannot satisfy this rule.

If WGC supplies no explicit publication date, the default safe result is `signal=0`, `confidence=0`, with `INSUFFICIENT HISTORY — publication date unavailable`. D/Q may approve a separate versioned schedule-bound rule later, but it must be labelled `estimated_release_bound`, carry a lower confidence, and never populate the true `publication_date` field.

## L8-001 — ETF net flows

- **Measured quantity:** global monthly net flow in physically backed gold ETFs, in tonnes. Do not substitute holdings level or change in flow.
- **Evidence window:** calendar month-end observations, not “last N workbook rows”. Missing months remain missing and do not compress the window.
- **Direction:** positive net flow → `+1`; negative net flow → `-1`; exact zero → `0`.
- **Horizon applicability:** 1-5d and 1-3m require a currently publication-verified monthly observation; 1-3y and 3-10y require the approved calendar history and are otherwise degraded.
- **Confidence:** deterministic sign is `1.0` only when the observation is publication-verified, current under the variable-specific stale rule, and the required calendar window is complete. Missing publication evidence, missing month, stale evidence, or parse ambiguity → `0.0`.
- **Caveat:** WGC reports both flows and holdings; the extractor must preserve the distinction and never infer flow from holdings without an approved method.

## L5-001 — official-sector purchases

- **Measured quantity:** aggregate monthly net changes in official gold holdings from canonical country rows, in tonnes. This is purchases minus sales, not an absolute holdings level.
- **Evidence window:** calendar month-end observations with late reporters and revisions retained as source facts. Do not use row-count lookbacks or silently fill missing months.
- **Direction:** positive net purchase → `+1`; negative net change → `-1`; exact zero → `0`.
- **Horizon applicability:** monthly data can inform 1-3m, 1-3y, and 3-10y only when the publication contract and required calendar history are satisfied; 1-5d is structurally weak and should be `0` with an explicit applicability note unless D/Q approve otherwise.
- **Confidence:** `1.0` only for an explicit publication date, complete required calendar window, and source-confirmed freshness. Unknown release date, late-reporter uncertainty, stale data, or insufficient history → `0.0`.
- **Revision rule:** a revised workbook replaces prior observations only with provenance showing the source file and source page; no revision may be hidden by cumulative caching.

## Shared degradation and evidence schema

Each variable JSON should retain `observation_date`, `publication_date` (nullable), `source_page_date` (nullable), `retrieved_at`, source URL, workbook identity, and a short evidence summary. If publication evidence is absent, emit `signal=0`, `confidence=0`, and explicitly announce `INSUFFICIENT HISTORY` or `STALE DATA`; never silently treat the data as fresh.

## Approval questions for D/Q

1. Should both variables remain zero-confidence until WGC exposes explicit publication evidence, or should a separately versioned conservative release-bound policy be approved?
2. Is L5-001 1-5d formally `NOT_APPLICABLE`, or should it remain applicable-but-degraded?
3. Should WGC page/article dates be retained only as provenance, or may they serve as an explicit publication date when the page clearly states the dataset update date?
