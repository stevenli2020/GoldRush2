# Test Quarantine Record

## Network snapshot fallback tests

**Tests:**

- `DR2_data_extraction/tests/test_l6_001.py::test_snapshot_fallback`
- `DR2_data_extraction/tests/test_l3_005.py::test_collector_snapshot_fallback`

**Objective:** Verify that the relevant collector returns a supplied local snapshot when the official source page/download is unavailable. L6-001 covers GPR; L3-005 covers the FOMC source.

**Reason for local isolation:** The original test does not mock the HTTP request. It therefore changes outcome depending on live internet availability: a successful request bypasses the fallback branch and makes the assertion fail. Running it in the ordinary WSL unit suite would make the result depend on external network state.

**Quarantine policy:** Exclude both from deterministic local unit runs, but do not delete them. Execute both in a dedicated network-integration job at least once per release and on collector changes. That job must force a simulated request failure for each fallback assertion, and separately run allowed live-source smoke checks with explicit network credentials/egress. The deterministic fallback assertions should be converted to HTTP-mocked tests before removing this record.
