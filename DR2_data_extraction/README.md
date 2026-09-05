# DR2 — Data Extraction

DR2 retrieves public-source data, keeps source-aware caches, and writes one current signal JSON for each variable.

Canonical implementation:

- [`src/goldrush2/collectors/`](../src/goldrush2/collectors/) — shared source collectors.
- [`src/goldrush2/extractors/`](../src/goldrush2/extractors/) — per-variable extraction rules.
- [`config/refresh_policies.yaml`](../config/refresh_policies.yaml) — refresh behavior.
- [`data/raw/`](../data/raw/), [`data/cache/`](../data/cache/), and [`data/current/`](../data/current/) — source, normalized, and current-output artifacts.

Run `gr2 collect` and `gr2 extract` from the repository root in WSL. Local historical DR2 inventory files, when present, remain at the repository root so that active source and cache work is not relocated.
