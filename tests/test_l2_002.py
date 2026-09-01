from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.collectors.fred import FredError, parse_observations
from goldrush2.extractors import l2_002


def observations(count=756, comparison_index=None, current=99.0, comparison=100.0):
    rows = [{"date": (date(2020, 1, 1) + timedelta(days=i)).isoformat(), "value": 100.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(99.0, 100.0, 1), (101.0, 100.0, -1), (100.0, 100.0, 0)])
def test_all_horizon_directions(horizon, lookback, current, comparison, signal):
    output = l2_002.build_output(observations(comparison_index=756 - lookback, current=current, comparison=comparison), as_of_date="2026-09-01")
    assert output["horizons"][horizon]["signal"] == signal
    assert output["horizons"][horizon]["confidence"] == 1


def test_schema_and_dates():
    output = l2_002.build_output(observations(6), as_of_date="2026-09-01")
    assert output["variable_id"] == "L2-002"
    assert output["observation_date"]
    assert set(output["horizons"]) == set(l2_002.HORIZON_LOOKBACKS)
    assert set(output["horizons"]["1-5d"]["evidence"]["data"]) == {"current_value", "current_date", "comparison_value", "comparison_date", "change_percentage_points"}


def test_missing_values_ignored():
    assert parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-01-02", "value": "118.9"}]}) == [{"date": "2026-01-02", "value": 118.9}]


def test_insufficient_history():
    output = l2_002.build_output(observations(4))
    assert output["horizons"]["1-5d"]["confidence"] == 0


def test_fresh_cache_fallback(monkeypatch, tmp_path):
    raw = tmp_path / "DTWEXBGS.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "118"}]}) + "\n")
    monkeypatch.setattr(l2_002, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l2_002.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert "SOURCE UNAVAILABLE" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache_output(monkeypatch, tmp_path):
    raw = tmp_path / "DTWEXBGS.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "118"}]}) + "\n")
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    monkeypatch.setattr(l2_002, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l2_002.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]
