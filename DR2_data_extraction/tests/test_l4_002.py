from datetime import date, timedelta
import json
import os
import time

import pytest

from goldrush2.dr2.collectors.fred import FredError, parse_observations
from goldrush2.dr2.extractors import l4_002


def monthly_observations(count=756, comparison_index=None, current=101.0, comparison=100.0):
    rows = [{"date": f"{2020 + i // 12:04d}-{i % 12 + 1:02d}-01", "value": 100.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(99.0, 100.0, 1), (101.0, 100.0, -1), (100.0, 100.0, 0)])
def test_all_monthly_horizon_directions(horizon, lookback, current, comparison, signal):
    output = l4_002.build_output(monthly_observations(comparison_index=756 - lookback, current=current, comparison=comparison), as_of_date="2026-09-01")
    assert output["horizons"][horizon]["signal"] == signal
    assert output["horizons"][horizon]["confidence"] == 1


def test_monthly_dates_and_index_schema():
    output = l4_002.build_output(monthly_observations(6), as_of_date="2026-09-01")
    assert output["data_frequency"] == "Monthly"
    assert output["observation_date"].endswith("-01")
    assert "change_absolute" in output["horizons"]["1-5d"]["evidence"]["data"]
    assert "Core PCE index" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_missing_values_are_ignored():
    parsed = parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-02-01", "value": "130.5"}]})
    assert parsed == [{"date": "2026-02-01", "value": 130.5}]


def test_insufficient_history():
    output = l4_002.build_output(monthly_observations(4))
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "valid monthly observations" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_fresh_cache_fallback(monkeypatch, tmp_path):
    raw = tmp_path / "PCEPILFE.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "130"}]}) + "\n")
    monkeypatch.setattr(l4_002, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l4_002.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert "SOURCE UNAVAILABLE" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache_output(monkeypatch, tmp_path):
    raw = tmp_path / "PCEPILFE.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "130"}]}) + "\n")
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    monkeypatch.setattr(l4_002, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    output = l4_002.run(raw_path=raw, output_path=tmp_path / "out.json")
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]
