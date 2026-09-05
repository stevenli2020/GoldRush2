"""Tests for the L7-005 SOFR-EFFR funding-stress extractor."""

from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.dr2.collectors.fred import FredError, parse_observations
from goldrush2.dr2.extractors import l7_005


def spread_observations(count: int = 756, *, current: float = 5.0, comparison: float = 4.0) -> list[dict[str, float | str]]:
    rows = []
    for index in range(count):
        spread = comparison if index == count - 5 else 4.5
        rows.append({"date": (date(2023, 1, 1) + timedelta(days=index)).isoformat(), "value": spread, "sofr": 5.0 + spread / 100, "effr": 5.0})
    rows[-1]["value"] = current
    rows[-1]["sofr"] = 5.0 + current / 100
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(5.0, 4.0, 1), (3.0, 4.0, -1), (4.0, 4.0, 0)])
def test_all_horizon_directions(horizon, lookback, current, comparison, signal):
    rows = spread_observations(current=current, comparison=4.0)
    rows[-lookback]["value"] = comparison
    result = l7_005.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1
    assert "change_basis_points" in result["horizons"][horizon]["evidence"]["data"]


def test_aligns_only_common_dates():
    sofr = [{"date": "2026-01-01", "value": 4.3}, {"date": "2026-01-02", "value": 4.4}]
    effr = [{"date": "2026-01-02", "value": 4.2}, {"date": "2026-01-03", "value": 4.1}]
    assert l7_005.align_spread_observations(sofr, effr) == [{"date": "2026-01-02", "value": pytest.approx(20.0), "sofr": 4.4, "effr": 4.2}]


def test_missing_values_are_excluded_from_alignment():
    sofr = parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-01-02", "value": "4.3"}]})
    effr = [{"date": "2026-01-01", "value": 4.0}, {"date": "2026-01-02", "value": 4.1}]
    assert [row["date"] for row in l7_005.align_spread_observations(sofr, effr)] == ["2026-01-02"]


def test_insufficient_common_history():
    assert l7_005.build_output(spread_observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_fresh_dependency_cache_fallback(monkeypatch, tmp_path):
    sofr_path, effr_path = tmp_path / "SOFR.json", tmp_path / "EFFR.json"
    payload = {"observations": [{"date": "2026-01-01", "value": "4"}]}
    sofr_path.write_text(json.dumps(payload), encoding="utf-8")
    effr_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(l7_005, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l7_005.run(output_path=tmp_path / "out.json", sofr_raw_path=sofr_path, effr_raw_path=effr_path)
    summary = output["horizons"]["1-5d"]["evidence"]["summary"]
    assert "SOURCE UNAVAILABLE" in summary
    assert "cached data used" in summary


def test_stale_dependency_cache(monkeypatch, tmp_path):
    sofr_path = tmp_path / "SOFR.json"
    sofr_path.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "4"}]}), encoding="utf-8")
    old = time.time() - 8 * 86400
    os.utime(sofr_path, (old, old))
    monkeypatch.setattr(l7_005, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l7_005.run(output_path=tmp_path / "out.json", sofr_raw_path=sofr_path, effr_raw_path=tmp_path / "EFFR.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_output_schema():
    result = l7_005.build_output(spread_observations())
    assert result["variable_id"] == "L7-005"
    assert result["data_frequency"] == "Daily"
    assert set(result["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}

