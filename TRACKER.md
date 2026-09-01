# GR2 Development Tracker

## Scope

GR2 uses exactly the 45 variables below across Layers L0-L10. The IDs and names are carried forward from GR1 except for the owner-approved restoration of L1-004 as 2Y TIPS Real Yield; variables outside this table are not part of GR2.

This tracker records GR2 work only. GR1 rules, statuses, and commit hashes do not establish GR2 completion.

## Roadmap status

| Roadmap | Deliverable | Status |
|---|---|---|
| DR1 | Define the 11 layers and 45 variables | Draft complete; owner review pending |
| DR2 | Shared source collectors and one current extractor JSON per variable | In progress - FRED collector and L1-001/L1-002/L1-007 complete (3/45); L1-004 in progress; L1-003 pending L1-004 |
| DR3 | Versioned fixed variable-weight schema and researched aggregation method | Not started |
| DR4 | Four current scores, confidence levels, and Gemini report | Not started |
| DR5 | One-command user workflow, inputs, outputs, and notifications | Not started |

## Variable tracker

`DR1` records the initial GR2 definition state. Source groups, extractor rules, freshness limits, and weight values remain deliberately blank until their roadmap work begins.

| # | Variable ID | Variable name | Concise GR2 definition | DR1 | DR2 | DR3 |
|---:|---|---|---|---|---|---|
| 1 | L0-001 | Above-Ground Gold Stock | Total accumulated above-ground gold and its change over time. | Carried forward | Not started | Not started |
| 2 | L0-002 | Central-Bank Gold Holdings | Gold held by central banks and official institutions. | Carried forward | Not started | Not started |
| 3 | L0-003 | Gold ETF Holdings | The stock of physical gold held by exchange-traded funds. | Carried forward | Not started | Not started |
| 4 | L0-005 | Bar-and-Coin Investment Holdings / Demand | Physical bar-and-coin investment demand and its contribution to market absorption. | Carried forward | Not started | Not started |
| 5 | L0-006 | Gold Recycling Flow | Gold returned to market through recycling and secondary supply. | Carried forward | Not started | Not started |
| 6 | L0-009 | Gold Lease Rates / Forward Rates | The cost and availability of borrowing or financing physical gold. | Carried forward | Not started | Not started |
| 7 | L1-001 | 10Y TIPS Real Yield | The inflation-adjusted yield on 10-year US Treasury securities. | Carried forward | Owner approved - FRED DFII10 | Not started |
| 8 | L1-002 | 5Y TIPS Real Yield | The inflation-adjusted yield on 5-year US Treasury securities. | Carried forward | Owner approved - FRED DFII5 | Not started |
| 9 | L1-003 | Forward Real Rates | Market-implied real interest rates for future periods. | Carried forward | Pending L1-004 | Not started |
| 10 | L1-004 | 2Y TIPS Real Yield | Federal Reserve Board estimate of the smoothed yield on hypothetical 2-year TIPS. | Owner-approved restoration | In progress - Federal Reserve Board TIPS Yield Curve | Not started |
| 11 | L1-005 | Treasury Term Premium | Estimated compensation for holding longer-duration US Treasury risk. | Carried forward | Not started | Not started |
| 12 | L1-006 | Expected Policy Rate | The expected policy-rate component of current real opportunity cost. | Carried forward | Not started | Not started |
| 13 | L1-007 | 5Y5Y Forward Real Rate | The expected five-year real rate beginning five years ahead. | Carried forward | Owner approved - derived from L1-001/L1-002 | Not started |
| 14 | L2-001 | DXY US Dollar Index | Dollar valuation against the major currencies represented in DXY. | Carried forward | Not started | Not started |
| 15 | L2-002 | Broad Trade-Weighted Nominal US Dollar Index | Dollar valuation against a broad trade-weighted currency basket. | Carried forward | Not started | Not started |
| 16 | L2-003 | USD/CNY | The dollar-renminbi exchange rate and its China purchasing-power channel. | Carried forward | Not started | Not started |
| 17 | L3-001 | Fed Funds Futures Expected Policy Rate | The future Federal Reserve policy path implied by Fed Funds futures. | Carried forward | Not started | Not started |
| 18 | L3-002 | OIS Forward Policy Curve | The future policy-rate path implied by overnight-index swaps. | Carried forward | Not started | Not started |
| 19 | L3-003 | Expected Terminal Policy Rate | The market-implied endpoint of the current monetary-policy cycle. | Carried forward | Not started | Not started |
| 20 | L3-004 | Probability Distribution of Future Policy Outcomes | Market-implied probabilities across possible future policy-rate outcomes. | Carried forward | Not started | Not started |
| 21 | L3-005 | FOMC Dot Plot Path | Federal Reserve participants' published policy-rate projections. | Carried forward | Not started | Not started |
| 22 | L3-006 | FOMC Statements / Forward-Guidance Signal | Gemini-derived direction from official FOMC statements and guidance. | Carried forward | Not started | Not started |
| 23 | L4-001 | CPI Inflation Rate | Headline US consumer-price inflation. | Carried forward | Not started | Not started |
| 24 | L4-002 | Core PCE Inflation Rate | The Federal Reserve's preferred underlying consumer-inflation measure. | Carried forward | Not started | Not started |
| 25 | L4-003 | 5Y Breakeven Inflation | Market-implied average inflation over the next five years. | Carried forward | Not started | Not started |
| 26 | L4-004 | 10Y Breakeven Inflation | Market-implied average inflation over the next ten years. | Carried forward | Not started | Not started |
| 27 | L4-006 | Fiscal Deficit / GDP | The government fiscal deficit relative to economic output. | Carried forward | Not started | Not started |
| 28 | L4-007 | Debt / GDP | Government debt relative to economic output. | Carried forward | Not started | Not started |
| 29 | L4-008 | Interest Expense / Government Revenue | Government interest costs relative to its revenue base. | Carried forward | Not started | Not started |
| 30 | L4-009 | Treasury Maturity Structure | The maturity composition and refinancing profile of US Treasury debt. | Carried forward | Not started | Not started |
| 31 | L5-001 | Monthly Official-Sector Gold Purchase Volume | Monthly gold purchases by central banks and other official institutions. | Carried forward | Not started | Not started |
| 32 | L5-002 | Gold Share of Official Reserves | Gold's share of total official reserve assets. | Carried forward | Not started | Not started |
| 33 | L5-003 | Reserve Composition Change / USD Share Change | Changes in the currency composition of official reserves, especially the dollar share. | Carried forward | Not started | Not started |
| 34 | L5-006 | Official-Sector Gold Sales / Lending | Gold supplied through official-sector sales, swaps, or lending. | Carried forward | Not started | Not started |
| 35 | L6-001 | Active Conflict and Escalation Signal | Gemini-derived assessment of active conflict and escalation affecting safe-haven demand. | Carried forward | Not started | Not started |
| 36 | L6-002 | Sanctions and Sovereign-Asset Freeze Events | Gemini-derived assessment of sanctions and asset restrictions affecting reserve security. | Carried forward | Not started | Not started |
| 37 | L7-001 | Major Central-Bank Balance-Sheet Liquidity | Realized liquidity supplied or withdrawn through major central-bank balance sheets. | Carried forward | Not started | Not started |
| 38 | L7-003 | Global Private Non-Financial Credit Growth | Growth in credit to private non-financial borrowers across major economies. | Carried forward | Not started | Not started |
| 39 | L7-004 | Credit-Spread Financial Stress | Credit-market risk and financial stress measured through borrowing spreads. | Carried forward | Not started | Not started |
| 40 | L7-005 | Treasury Repo Funding Stress | Stress in secured short-term US Treasury funding markets. | Carried forward | Not started | Not started |
| 41 | L8-001 | Gold ETF Net Flows | Current investment money flowing into or out of gold ETFs. | Carried forward | Not started | Not started |
| 42 | L9-001 | Shanghai Gold Exchange Premium/Discount | The local Chinese physical gold price relative to the international benchmark. | Carried forward | Not started | Not started |
| 43 | L9-004 | India Physical Gold Imports and Consumer Demand | Indian gold imports and consumer acquisition as a regional physical-demand signal. | Carried forward | Not started | Not started |
| 44 | L10-001 | COMEX Managed-Money Net Positioning | Net speculative futures positioning reported for COMEX gold. | Carried forward | Not started | Not started |
| 45 | L10-002 | COMEX Gold Futures Open Interest | Outstanding COMEX gold futures contracts and associated market participation. | Carried forward | Not started | Not started |

## DR2 implementation evidence

| Date | Variable | Collector and extractor | Freshness and degradation | Verification | Owner decision |
|---|---|---|---|---|---|
| 2026-09-01 | L1-001 | Shared FRED `series_observations` collector for `DFII10`; lookbacks 5, 63, 252, and 756 valid observations | Live source overwrites the raw response; failed collection uses cache younger than 7 days; older cache returns `STALE DATA` with zero confidence | 17 tests passed in WSL; live FRED run returned 6,172 raw observations and latest observation date 2026-08-28; all four horizon outputs validated | Approved by Steven on 2026-09-01 |
| 2026-09-01 | L1-002 | Reused shared FRED `series_observations` collector for `DFII5`; lookbacks 5, 63, and 252 valid observations; `3-10y` structurally inapplicable | Live source overwrites the raw response; failed collection uses cache younger than 7 days; older cache returns `STALE DATA` with zero confidence for applicable horizons | 8 focused L1-002 tests and 25 combined tests passed in WSL; live FRED run returned 6,172 raw observations and latest observation date 2026-08-28; all four horizon outputs validated | Approved by Steven on 2026-09-01 |
| 2026-09-01 | L1-007 | Derived from current L1-001 `DFII10` and L1-002 `DFII5` caches using the approved 5Y5Y no-arbitrage formula; lookbacks 5, 63, 252, and 756 aligned observations | No raw cache of its own; stale or zero-confidence dependency returns `STALE DEPENDENT DATA`/`DEPENDENCY FAILED`; fresh dependency caches are annotated in evidence | 11 focused L1-007 tests and 36 combined tests passed in WSL; live output formula and four horizons validated with latest underlying date 2026-08-28 | Approved by Steven on 2026-09-01 |

## Tracker rules

- Work source-group by source-group during DR2; define the groups when DR2 starts.
- A variable is not DR2-complete until its collector dependency, extractor, current JSON, freshness behavior, degraded-output behavior, and WSL verification are complete.
- Do not infer DR3 completion from DR2 completion.
- Record the active Weight Schema version when DR3 begins.
- Update this tracker as part of each completed implementation task.
- Commit and push each completed, verified task automatically when implementation was explicitly requested.
