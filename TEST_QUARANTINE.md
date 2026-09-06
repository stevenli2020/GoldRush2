# Test Quarantine Record

## `test_snapshot_fallback`

**Test:** `DR2_data_extraction/tests/test_l6_001.py::test_snapshot_fallback`

**Objective:** Verify that `GPRCollector.fetch()` returns the supplied local snapshot when the official GPR page/download is unavailable.

**Reason for local isolation:** The original test does not mock the HTTP request. It therefore changes outcome depending on live internet availability: a successful request bypasses the fallback branch and makes the assertion fail. Running it in the ordinary WSL unit suite would make the result depend on external network state.

**Quarantine policy:** Exclude it from deterministic local unit runs, but do not delete it. Execute it in a dedicated network-integration job at least once per release and on collector changes. That job must force a simulated request failure for the fallback assertion, and separately run an allowed live-source smoke check with explicit network credentials/egress. The deterministic fallback assertion should be converted to an HTTP-mocked test before removing this record.
