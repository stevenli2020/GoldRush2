# Tranche 3 Phase B — Exhaustive Target Variable List

**Status:** proposed; frozen only after D/Q approval

Phase B will touch exactly these 18 variable IDs and no others:

1. L0-002
2. L0-003
3. L0-005
4. L0-006
5. L1-005
6. L3-005
7. L4-001
8. L4-002
9. L4-006
10. L4-007
11. L4-009
12. L5-001
13. L5-002
14. L5-003
15. L5-006
16. L7-003
17. L8-001
18. L9-004

The anti-leakage baseline will exclude these exact target files from the protected set and will protect every other `data/current/*.json` file by SHA-256 and mtime. No wildcard, `etc.`, or implicit additional variable is authorized.
