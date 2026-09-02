# GoldRush2

GoldRush2 is a small, Python-first personal commodity-investment advisory MVP. It produces current evidence and directional inputs; it does not execute trades or retain historical outlooks.

## Collection cache strategy

Collection separates three kinds of artifacts:

- `data/raw/` stores source API responses and downloaded workbooks for debugging and replay.
- `data/cache/<variable>/` stores normalized observations and `_meta.json` for refresh decisions.
- `data/current/` stores variable signal JSON created by extractors, not by collection refreshes.

`config/refresh_policies.yaml` assigns each implemented source variable either `always_refresh` or `check_last_observation_date`. The latter checks the source's newest observation before requesting more data; FRED and Yahoo then use incremental requests where available. A source failure preserves the normalized cache and prints a warning. `--force` requests a full refresh and records `force_refreshed_at`.

Run collection from WSL after loading `.env`:

```bash
source .venv/bin/activate
set -a; source .env; set +a
gr2 collect L4-001
gr2 collect L4-001 --force
gr2 collect L4-001 -v       # major refresh decisions
gr2 collect L4-001 -vv      # source and date details
gr2 collect L4-001 -vvv     # cache paths and metadata
gr2 collect --all --dry-run
```

The mixed CME/FRED L1-006 collector remains internal to its existing extractor and is reported as delegated by `gr2 collect`.

## Extractor commands

The extraction command discovers every `l<layer>_<variable>` module under
`src/goldrush2/extractors`, so adding a module automatically makes its variable
available without another CLI mapping entry. Each discovered module must expose
the existing `run()` function and writes its result to `data/current/`.

```bash
gr2 extract L0-006             # write the file and print a one-line summary
gr2 extract L7-003 --print     # write the file and print compact JSON
gr2 extract L7-003 --pretty    # write the file and print indented JSON
gr2 extract --check            # list discovered modules and mapping status
```
