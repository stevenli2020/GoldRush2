from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.dr2.collectors.fred import FredError, parse_observations
from goldrush2.dr2.extractors import l4_004


def observations(count=756, comparison_index=None, current=1.0, comparison=2.0):
    rows = [{"date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(), "value": 0.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(1.0, 2.0, 1), (3.0, 2.0, -1), (2.0, 2.0, 0)])
def test_all_horizons_signal_directions(horizon, lookback, current, comparison, signal):
    output = l4_004.build_output(observations(comparison_index=756 - lookback, current=current, comparison=comparison), as_of_date="2026-09-01")
    assert output["horizons"][horizon]["signal"] == signal
    assert output["horizons"][horizon]["confidence"] == 1


def test_missing_values_are_ignored_by_fred_parser():
    parsed = parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-01-02", "value": "2.1"}]})
    assert parsed == [{"date": "2026-01-02", "value": 2.1}]


def test_insufficient_history_and_schema():
    output = l4_004.build_output(observations(4), as_of_date="2026-09-01")
    assert output["variable_id"] == "L4-004"
    assert set(output["horizons"]) == set(l4_004.HORIZON_LOOKBACKS)
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert set(output["horizons"]["1-5d"]["evidence"]["data"]) == {"current_value", "current_date", "comparison_value", "comparison_date", "change_percentage_points"}


def test_fresh_cache_fallback(monkeypatch, tmp_path):
    raw = tmp_path / "T10YIE.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "2"}]}) + "\n")
    monkeypatch.setattr(l4_004, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l4_004.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert "SOURCE UNAVAILABLE" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache_degrades(monkeypatch, tmp_path):
    raw = tmp_path / "T10YIE.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "2"}]}) + "\n")
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    monkeypatch.setattr(l4_004, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l4_004.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]
