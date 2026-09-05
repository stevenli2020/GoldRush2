import json
import os
import time
from datetime import date

import pytest

from goldrush2.dr2.collectors.fred import FredError, parse_observations
from goldrush2.dr2.extractors import l4_007


def observations(count=20, comparison_index=None, current=120.0, comparison=118.0):
    rows = [{"date": f"{2020 + i // 4:04d}-{1 + (i % 4) * 3:02d}-01", "value": 118.0} for i in range(count)]
    if comparison_index is not None:
        rows[comparison_index]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-3y", 8), ("3-10y", 20)])
@pytest.mark.parametrize("current, comparison, signal", [(117.0, 118.0, 1), (120.0, 118.0, -1), (118.0, 118.0, 0)])
def test_quarterly_signal_directions(horizon, lookback, current, comparison, signal):
    result = l4_007.build_output(observations(comparison_index=20 - lookback, current=current, comparison=comparison))
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def test_short_horizons_are_inapplicable():
    result = l4_007.build_output(observations(2))
    assert result["horizons"]["1-3m"]["signal"] == 0
    assert result["horizons"]["1-3m"]["confidence"] == 1
    assert result["horizons"]["1-3m"]["evidence"]["data"]["current_value"] is None


def test_schema_and_quarterly_dates():
    result = l4_007.build_output(observations(20), as_of_date="2026-09-01")
    assert result["variable_id"] == "L4-007"
    assert result["data_frequency"] == "Quarterly"
    assert result["horizons"]["1-3y"]["evidence"]["data"]["change_absolute"] is not None


def test_missing_values_ignored():
    assert parse_observations({"observations": [{"date": "2026-01-01", "value": "."}, {"date": "2026-04-01", "value": "122.5"}]}) == [{"date": "2026-04-01", "value": 122.5}]


def test_insufficient_history():
    result = l4_007.build_output(observations(7))
    assert result["horizons"]["1-3y"]["confidence"] == 0


def test_empty_series_degrades_applicable_horizons():
    result = l4_007.build_output([])
    assert result["observation_date"] is None
    assert result["horizons"]["3-10y"]["confidence"] == 0


def test_twenty_quarter_lookback_uses_first_observation():
    result = l4_007.build_output(observations(20))
    assert result["horizons"]["3-10y"]["evidence"]["data"]["comparison_date"] == "2020-01-01"


def test_cached_valid_result_is_annotated():
    result = l4_007.build_output(observations(20), cached=True)
    assert "cached data used" in result["horizons"]["1-3y"]["evidence"]["summary"]


def test_fresh_and_stale_cache(monkeypatch, tmp_path):
    raw = tmp_path / "GFDEGDQ188S.json"
    raw.write_text(json.dumps({"observations": [{"date": "2026-01-01", "value": "122"}]}) + "\n")
    monkeypatch.setattr(l4_007, "fetch_series", lambda *args, **kwargs: (_ for _ in ()).throw(FredError("offline")))
    fresh = l4_007.run(raw_path=raw, output_path=tmp_path / "fresh.json")
    assert "SOURCE UNAVAILABLE" in fresh["horizons"]["1-5d"]["evidence"]["summary"]
    old = time.time() - 8 * 86400
    os.utime(raw, (old, old))
    stale = l4_007.run(raw_path=raw, output_path=tmp_path / "stale.json")
    assert stale["horizons"]["1-3y"]["confidence"] == 0
    assert "STALE DATA" in stale["horizons"]["1-3y"]["evidence"]["summary"]
