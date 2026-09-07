# Tranche 3 Phase B — Legacy Output Schema Remediation

**Decision:** Option A — standardize the legacy outputs.

The 16 legacy variables are normalized at the `gr2 extract` output boundary. For each horizon, the CLI now guarantees `signal`, `confidence`, `status`, and `evidence`. Existing extractor values are preserved; only the missing status field is added.

Status mapping is deterministic:

- evidence summary containing `does not support` → `NOT_APPLICABLE`;
- confidence greater than zero → `VALID`;
- otherwise → `INSUFFICIENT_HISTORY`.

This is a compatibility remediation, not a fallback that silently upgrades data. The DR3 aggregator therefore receives explicit status-bearing JSON for these variables. No strategy rerun was performed.

The 16 normalized IDs are: L0-002, L0-003, L0-005, L0-006, L1-005, L3-005, L4-001, L4-002, L4-006, L4-007, L4-009, L5-002, L5-003, L5-006, L7-003, L9-004.
