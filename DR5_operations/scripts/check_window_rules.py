"""Fail when approved extractor window contracts are missing or stale."""
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "DR2_data_extraction/src/goldrush2/dr2/extractors"
FORBIDDEN = ("252", "756")
errors = []
for path in TARGET.glob("*.py"):
    text = path.read_text(encoding="utf-8")
    if path.name == "l4_006.py" and ("{\"1-3y\": 12, \"3-10y\": 40}" not in text):
        errors.append(f"{path}: L4-006 must use 12/40")
    if "HORIZON_LOOKBACKS" in text and any(re.search(rf"\\b{n}\\b", text) for n in FORBIDDEN):
        errors.append(f"{path}: legacy 252/756 lookback reference")
if errors:
    print("Window rule check failed:")
    print("\n".join(errors))
    sys.exit(1)
print("Window rule check passed")
