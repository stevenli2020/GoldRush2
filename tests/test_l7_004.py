from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.collectors.fred import FredError, parse_observations
from goldrush2.extractors import l7_004


def observations(count=756, comparison_index=None, current=6.0, comparison=5.0):
    rows = [{"date": (date(2023, 1, 1) + timedelta(days=i)).isoformat(), "value": 5.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(6.0, 5.0, 1), (4.0, 5.0, -1), (5.0, 5.0, 0)])
def test_all_horizon_directions(horizon, lookback, current, comparison, signal):
    result = l7_004.build_output(observations(comparison_index=756 - lookback, current=current, comparison=comparison))
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1
    assert "change_pct" in result["horizons"][horizon]["evidence"]["data"]


def test_daily_schema():
    result = l7_004.build_output(observations(6), as_of_date="2026-09-01")
    assert result["data_frequency"] == "Daily"
    assert result["variable_id"] == "L7-004"


def test_missing_values_ignored():
    assert parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-01-02", "value": "3.1"}]}) == [{"date": "2026-01-02", "value": 3.1}]


def test_insufficient_history():
    assert l7_004.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_fresh_cache_fallback(monkeypatch, tmp_path):
    raw = tmp_path / "BAMLH0A0HYM2.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "3"}]}) + "\n")
    monkeypatch.setattr(l7_004, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l7_004.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert "SOURCE UNAVAILABLE" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache_output(monkeypatch, tmp_path):
    raw = tmp_path / "BAMLH0A0HYM2.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "3"}]}) + "\n")
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    monkeypatch.setattr(l7_004, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l7_004.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]
