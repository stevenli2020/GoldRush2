# Tranche 3 Final Pytest Log

Command:

```bash
wsl bash -lc 'cd /mnt/d/Projects/GoldRush2 && .venv/bin/pytest -q -k "not snapshot_fallback"'
```

Final complete-run result:

```text
840 passed, 2 deselected, 991 warnings in 34.86s
```

The two deselected tests are the documented network snapshot fallback tests in `TEST_QUARANTINE.md`. Exit status was 0. No test failures occurred.
