from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.dr2.extractors import l2_001
from goldrush2.dr2.collectors import yahoo


def observations(count=756, comparison_index=None, current=99.0, comparison=100.0):
    rows = [{"date": (date(2020, 1, 1) + timedelta(days=i)).isoformat(), "value": 100.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(99.0, 100.0, 1), (101.0, 100.0, -1), (100.0, 100.0, 0)])
def test_all_horizon_directions(horizon, lookback, current, comparison, signal):
    result = l2_001.build_output(observations(comparison_index=756 - lookback, current=current, comparison=comparison), as_of_date="2026-09-01")
    item = result["horizons"][horizon]
    assert item["signal"] == signal
    assert item["confidence"] == 1
    assert "change_pct" in item["evidence"]["data"]


def test_schema_and_source():
    result = l2_001.build_output(observations(6), as_of_date="2026-09-01")
    assert result["variable_id"] == "L2-001"
    assert result["source_name"].startswith("Yahoo Finance DX-Y.NYB")
    assert set(result["horizons"]) == set(l2_001.HORIZON_LOOKBACKS)


def test_insufficient_history():
    assert l2_001.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_cached_annotation(monkeypatch):
    monkeypatch.setattr(yahoo, "fetch_yahoo_series", lambda symbol, path: observations(6))
    monkeypatch.setattr(yahoo, "LAST_FETCH_USED_CACHE", True)
    output = l2_001.run(output_path=l2_001.OUTPUT_PATH.parent / "test-L2-001.json", raw_path=l2_001.RAW_PATH)
    assert "cached data used" in output["horizons"]["1-5d"]["evidence"]["summary"]
    (l2_001.OUTPUT_PATH.parent / "test-L2-001.json").unlink(missing_ok=True)


def test_source_failure_degrades(monkeypatch, tmp_path):
    monkeypatch.setattr(yahoo, "fetch_yahoo_series", lambda symbol, path: (_ for _ in ()).throw(yahoo.YahooError("offline")))
    output = l2_001.run(raw_path=tmp_path / "missing.json", output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
