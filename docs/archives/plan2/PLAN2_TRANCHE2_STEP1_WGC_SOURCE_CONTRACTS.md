# Plan 2 Tranche 2 Step 1 — WGC Source Contracts (Draft)

**Status:** draft for D/Q review; no extractor changes
**Scope:** L8-001 ETF net flows and L5-001 official-sector net purchases
**Shared collector rule:** one WGC download/normalization path may serve both extractors; the workbook must not be downloaded or parsed independently for each variable.

## Publication-date finding

The WGC pages expose page/article dates and update schedules, but the public XLSX download links and workbook sheets inspected for this tranche do not expose a stable, observation-level `publication_date` field or an API release timestamp. The filename (`ETF_Flows_...xlsx` or `Changes_...xlsx`) is a source identifier, not proof of release time. HTTP response time, local file modification time, and system time are never accepted as `publication_date`.

Therefore this tranche must distinguish:

- `observation_date`: the month-end period measured in the workbook;
- `source_page_date`: an explicitly displayed WGC page/article date, retained as provenance only;
- `publication_date`: an explicit source release date, accepted only if present in page metadata, a release calendar, or a response field;
- `retrieved_at`: local audit metadata, never an economic availability date.

When no explicit publication date is available, the output is publication-unverified and must not receive full-confidence time-aligned evidence. A hard-coded empirical lag is allowed only as a documented conservative eligibility bound, not as a fabricated publication date; this draft does not authorize one yet.

## Contract table

| Variable | Public source | Quantity and unit | Source-stated cadence/lag | Publication metadata status | Current implementation gap |
|---|---|---|---|---|---|
| L8-001 | [WGC Gold ETF: Stock, Holdings and Flows](https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows) | Global monthly ETF net flow, tonnes; retain USD only as source evidence if available | WGC states weekly and monthly updates; monthly Excel is usually available within one week of previous month-end | No stable row-level/API publication date identified; page provides schedule, not a per-row release timestamp | Shared collector uses workbook discovery/cache mtime and extractor uses row-count lookbacks; neither creates a publication contract |
| L5-001 | [WGC Central Banks Gold Reserves by Country](https://www.gold.org/goldhub/data/gold-reserves-by-country) | Global monthly official-sector net purchases, tonnes; aggregate canonical country changes | WGC states monthly files are updated within the first 10 days, with data two months in arrears; revisions and late reporters are possible | No stable row-level/API publication date identified; page provides update schedule and data-as-of context | Shared collector uses workbook discovery/cache mtime and extractor uses row-count lookbacks; neither records release evidence |

## Required Step 1 decisions

1. The shared WGC collector must preserve the exact download URL, source page URL, workbook filename, observation coverage, explicit page date (if present), and retrieval timestamp as separate provenance fields.
2. It must not set `publication_date` from filename tokens, HTTP `Date`, filesystem mtime, or retrieval time.
3. If a later implementation adds a WGC release-calendar/page parser, its extracted date must be stored with the page URL and extraction evidence; absent that evidence, `publication_date` remains null.
4. Cached workbooks may be used only with an explicit cache status. A fresh local cache is not proof that the source was freshly published.
5. Before Step 3, D/Q must decide whether publication-unverified observations are excluded (`confidence=0`) or whether a conservative, versioned schedule bound may be used for eligibility. The latter must remain visibly labelled as an estimate and must never be called a publication date.

## Acceptance evidence for Step 2

- Source page and workbook links resolve to the intended WGC datasets.
- Workbook observation periods and units are independently verified.
- Publication metadata is either captured from an explicit source field/page evidence or documented as unavailable.
- Revision behavior, late reporters, and flow-versus-change semantics are recorded before code changes.
