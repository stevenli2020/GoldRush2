from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.collectors.fred import FredError, parse_observations
from goldrush2.extractors import l2_003


def observations(count=756, comparison_index=None, current=7.0, comparison=7.2):
    rows = [{"date": (date(2020, 1, 1) + timedelta(days=i)).isoformat(), "value": 7.2} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(7.0, 7.2, 1), (7.4, 7.2, -1), (7.2, 7.2, 0)])
def test_all_horizon_directions_and_change_pct(horizon, lookback, current, comparison, signal):
    result = l2_003.build_output(observations(comparison_index=756 - lookback, current=current, comparison=comparison), as_of_date="2026-09-01")
    item = result["horizons"][horizon]
    assert item["signal"] == signal
    assert item["confidence"] == 1
    assert "change_pct" in item["evidence"]["data"]


def test_schema_and_source():
    result = l2_003.build_output(observations(6), as_of_date="2026-09-01")
    assert result["variable_id"] == "L2-003"
    assert result["source_url"].endswith("DEXCHUS")
    assert set(result["horizons"]) == set(l2_003.HORIZON_LOOKBACKS)


def test_missing_values_are_ignored():
    assert parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-01-02", "value": "7.2"}]}) == [{"date": "2026-01-02", "value": 7.2}]


def test_insufficient_history():
    assert l2_003.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_fresh_cache_fallback(monkeypatch, tmp_path):
    raw = tmp_path / "DEXCHUS.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "7.2"}]}) + "\n")
    monkeypatch.setattr(l2_003, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l2_003.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert "SOURCE UNAVAILABLE" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache_output(monkeypatch, tmp_path):
    raw = tmp_path / "DEXCHUS.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "7.2"}]}) + "\n")
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    monkeypatch.setattr(l2_003, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l2_003.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]
