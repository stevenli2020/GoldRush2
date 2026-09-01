# GoldRush2 Project Definition

## 1. Purpose

GoldRush2 (`GR2`) is a personal commodity-investment decision-support tool. It produces a current directional outlook for gold across four time horizons, supported by concise evidence and confidence levels.

GoldRush (`GR1`) is reference material only. GR2 is an independent project and has no runtime dependency on GR1.

GR2 is deliberately an MVP:

- keep the system simple, usable, and deliverable;
- do not add institutional controls, hashing, historical replay, backtesting, or speculative features;
- use free and publicly accessible data sources;
- use existing open-source libraries and GR1 knowledge where useful;
- allow `yfinance`, OpenBB, and other suitable open resources;
- keep the user, not the software, responsible for the investment decision.

## 2. Fixed scope

GR2 uses only the 45 variables listed in `TRACKER.md`. Their layer numbers, variable IDs, and names remain unchanged except for the owner-approved restoration of L1-004 as 2Y TIPS Real Yield.

The four horizons are `1-5d`, `1-3m`, `1-3y`, and `3-10y`.

GR2 produces a current outlook only. It does not preserve past outlooks or reconstruct historical scores.

## 3. The 11 layers

| Layer | Name | Concise GR2 definition |
|---|---|---|
| L0 | Gold's Stock/Flow Monetary Architecture | The available gold stock, its ownership, mobility, and the physical flows that change supply available to the market. |
| L1 | Real Interest Rates and Opportunity Cost | The real return available from competing safe assets and the opportunity cost of holding non-yielding gold. |
| L2 | US Dollar and Global FX Regime | Dollar valuation and currency purchasing-power channels that affect the gold price and non-US demand. |
| L3 | Monetary Policy Expectations | Expected changes in the future policy path and the market or official evidence that causes policy repricing. |
| L4 | Inflation, Purchasing Power, and Fiscal Credibility | Inflation expectations, currency purchasing-power risk, and fiscal conditions that affect confidence in sovereign money and debt. |
| L5 | Official-Sector Reserve Allocation | Gold purchases, sales, lending, and reserve-composition decisions by central banks and other official institutions. |
| L6 | Geopolitical Transmission Channels | Conflict, sanctions, and sovereign-asset restrictions that affect safe-haven demand and reserve security. |
| L7 | Global Liquidity and Financial Conditions | Realized liquidity, credit creation, risk-bearing capacity, and funding stress in the financial system. |
| L8 | Investment Flows | Direct allocation into or out of gold investment vehicles, kept distinct from the stock of gold already held. |
| L9 | Regional Physical-Market Dynamics | Local premiums, imports, and consumer demand that reveal physical-market tightness in major gold markets. |
| L10 | Market Microstructure and Derivatives | Futures positioning, open interest, leverage, and market activity that can amplify gold-price moves. |

GR1 Layer 11 is outside GR2 because none of its variables appears in the agreed 45-variable tracker.

## 4. Development roadmap

### DR1 — Define layers and variables

- Carry forward the 11 layers and 45 variables identified above.
- Preserve IDs and names.
- Simplify definitions where doing so improves clarity without changing the variable's economic meaning.
- Treat `PROJECT.md` and `TRACKER.md` as GR2's self-contained definition; GR1 remains background reference.

### DR2 — Data extraction

- Build shared collectors grouped by data source.
- Define the source groups only when DR2 begins.
- Give every variable its own extractor.
- Prefer Python replacements for GR1 TypeScript scripts.
- Retain only the latest successful raw response for each collector, overwriting it on the next successful collection.
- Retain no raw-data history, manifests, or hashes.
- Write one current JSON file per variable, overwriting the prior variable JSON on every run.

Only `L3-006`, `L6-001`, and `L6-002` are qualitative and Gemini-derived in Version 1. They use the same bounded, structured assessment pattern established for GR1's `L3-006`, adapted to the GR2 JSON contract. GR2 has no multi-provider abstraction. The other 41 variables are deterministic.

### DR3 — Data analytics

- Research and define the contribution-weight algorithm.
- Store weights in a versioned schema.
- Version 1 uses fixed weights assigned directly to individual variables for each horizon.
- Variable weights sum to `1.0` within each horizon.
- Version 1 has no separate layer weights, interaction adjustments, dynamic regime selection, or automatic switching between weight versions.
- The exact formula connecting weights, signals, and confidence is deliberately deferred for deeper research and owner discussion.

### DR4 — Data presentation

- Produce one deterministic score for each horizon on a scale from `-100` to `+100`.
- Negative scores are bearish for gold, zero is neutral, and positive scores are bullish.
- Store confidence internally from `0.0` to `1.0` and display it from `0%` to `100%`.
- Overwrite `current_scores.json` on each run.
- Use Gemini to generate `current_report.md`, overwriting the previous report.
- Limit the report to 5,000 words.
- Restrict the report to the current run's DR2 evidence and DR3/DR4 results. Gemini must not add unsupported outside facts or conduct separate web research.
- Present outlook and evidence only. Do not issue buy/sell instructions, size positions, or execute trades.

### DR5 — Operational design

- Provide one Python command that runs collection, extraction, analytics, scoring, and reporting end to end.
- Read settings and credentials from GR2 configuration and GR2's ignored `.env` file.
- Never read GR1 files or credentials at runtime.
- At completion, display the four scores and confidence levels, the output locations, and every stale, missing, failed, or credential-blocked variable.

## 5. DR2 variable JSON contract

Each variable JSON uses this minimal structure:

```json
{
  "variable_id": "L1-001",
  "as_of_date": "2026-09-01",
  "sources": [
    {
      "name": "FRED - 10-Year TIPS Yield (DFII10)",
      "url": "https://fred.stlouisfed.org/series/DFII10",
      "observation_date": "2026-08-31"
    }
  ],
  "horizons": {
    "1-5d": {
      "signal": 1,
      "confidence": 1.0,
      "evidence": {
        "data": {
          "latest_value": 1.72,
          "comparison_value": 1.81,
          "change": -0.09,
          "unit": "percent"
        },
        "summary": "The 10-year real yield fell, which is supportive for gold."
      }
    },
    "1-3m": {
      "signal": 0,
      "confidence": 1.0,
      "evidence": {
        "data": {
          "example": "variable-specific facts"
        },
        "summary": "Brief evidence explanation."
      }
    },
    "1-3y": {
      "signal": 0,
      "confidence": 1.0,
      "evidence": {
        "data": {
          "example": "variable-specific facts"
        },
        "summary": "Brief evidence explanation."
      }
    },
    "3-10y": {
      "signal": 0,
      "confidence": 1.0,
      "evidence": {
        "data": {
          "applicable": false
        },
        "summary": "This horizon is structurally inapplicable, so its deterministic signal is neutral."
      }
    }
  }
}
```

Contract rules:

- `signal` is always `-1`, `0`, or `1`.
- Fresh deterministic results use confidence `1.0`.
- Qualitative Gemini-derived results use confidence from `0.0` to `1.0`.
- A structurally inapplicable horizon uses signal `0` and confidence `1.0` because neutrality is an intentional deterministic rule.
- Stale, missing, failed, credential-blocked, or AI-unavailable results use signal `0` and confidence `0.0`.
- A degraded result's summary must begin with a clear label such as `STALE DATA`, `MISSING DATA`, `EXTRACTION FAILED`, `CREDENTIAL MISSING`, `CREDENTIAL EXPIRED`, or `AI UNAVAILABLE`.
- `evidence.data` contains the smallest useful machine-readable facts and may vary by variable.
- `evidence.summary` is required and briefly explains the facts, comparison, direction, or problem.
- `sources` stays minimal: source name, direct public URL, and observation date. It is a list because some variables use multiple sources.

## 6. Freshness and partial failure

- Define freshness limits separately for each variable according to its publication schedule.
- Check the source on every run when it is reachable.
- A date beyond the normal freshness limit does not make an observation stale when the source confirms it remains the latest published value.
- If the source is unreachable, the latest stored response may be used only while it remains within the variable's normal freshness limit.
- Once beyond that limit, live source verification is required; otherwise return signal `0`, confidence `0.0`, and `STALE DATA - SOURCE UNREACHABLE`.
- A missing or expired credential degrades only the dependent variables and does not stop the full run.
- If Gemini is unavailable, the 41 deterministic variables still run. The three qualitative variables return signal `0`, confidence `0.0`, and `AI UNAVAILABLE`; the CLI clearly states that the narrative report could not be generated.

## 7. Credentials and dependencies

GR2 keeps its own ignored `.env` containing copies of the credentials it needs, such as the Gemini API key, FRED API key, and source-specific session cookies. Credential values are never committed or written into documentation. Exact environment-variable names will be defined with the relevant collectors during DR2.

GR2 is Python-first across collectors, extractors, analytics, presentation, and operation. TypeScript is allowed only when Python cannot reasonably provide the required capability. Prefer established project dependencies over custom implementations.

## 8. Delivery and governance

- Follow `AGENTS.md`.
- Make the smallest change that completes the active task.
- Verify implementation in WSL.
- Keep design decisions, implementation, verification, and owner approval distinct.
- For an explicitly requested implementation task, commit and push each completed, verified unit automatically.
- The owner may request an interim commit and push before the larger task is complete.
- Do not add a feature unless omitting it would materially damage the project.

## 9. Deferred decisions

The following are intentionally not decided in this definition:

- DR2 data-source groups and their implementation order;
- variable-specific extractors, freshness limits, and signal rules;
- the Weight Schema Version 1 values;
- the DR3 formula connecting weights, signals, and confidence;
- future weight-schema versions or dynamic selection behavior;
- features beyond the current-outlook command-line MVP.
