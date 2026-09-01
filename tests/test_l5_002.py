"""Tests for the historical L5-002 cumulative reserve-change proxy."""

from datetime import datetime

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l5_002


def observations(count=756, current=200.0, comparison=100.0):
    rows = [{"date": f"{2000 + i // 12:04d}-{i % 12 + 1:02d}-01", "value": 150.0} for i in range(count)]
    if count >= 5:
        rows[-5]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(200.0, 100.0, 1), (50.0, 100.0, -1), (100.0, 100.0, 0)])
def test_directions_and_lookbacks(horizon, lookback, current, comparison, signal):
    rows = observations(current=current)
    rows[-lookback]["value"] = comparison
    result = l5_002.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def changes_workbook(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Monthly"
    sheet.append([None, "Country", None, datetime(2002, 1, 1), datetime(2002, 2, 1), datetime(2002, 3, 1)])
    sheet.append([None, "US", None, 10.0, -2.0, 3.0])
    sheet.append([None, "Turkey*", None, 100.0, 100.0, 100.0])
    sheet.append([None, "Turkey", None, 2.0, -1.0, 1.0])
    path = tmp_path / "Changes_latest_as_of_test_IFS.xlsx"
    workbook.save(path)
    return path


def test_parser_uses_changes_only_cumulative_fallback(tmp_path):
    assert l5_002.parse_reserve_share_workbook(changes_workbook(tmp_path), cache_path=tmp_path / "parsed.json")[-1] == {"date": "2002-03-01", "value": 13.0}


def test_parser_reuses_shared_persistent_cache(tmp_path, monkeypatch):
    workbook = changes_workbook(tmp_path)
    cache_path = tmp_path / "parsed.json"
    expected = l5_002.parse_reserve_share_workbook(workbook, cache_path=cache_path)
    monkeypatch.setattr("goldrush2.extractors._wgc_common.parse_official_changes_workbook", lambda path: (_ for _ in ()).throw(AssertionError("XLSX was parsed again")))
    assert l5_002.parse_reserve_share_workbook(workbook, cache_path=cache_path) == expected


def test_proxy_is_explicit_and_not_fraction_claim():
    result = l5_002.build_output(observations())
    assert "proxy" in result["source_name"]
    assert "denominator" in result["calculation_note"]
    assert result["calculation_method"] == "cumulative_net_changes_proxy_from_2000-01"


def test_insufficient_history():
    assert l5_002.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_source_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(l5_002.wgc, "fetch_wgc_official_changes", lambda path: None)
    monkeypatch.setattr(l5_002.wgc, "LAST_FETCH_STALE", False)
    result = l5_002.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["1-5d"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in result["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(l5_002.wgc, "fetch_wgc_official_changes", lambda path: None)
    monkeypatch.setattr(l5_002.wgc, "LAST_FETCH_STALE", True)
    result = l5_002.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert "STALE DATA" in result["horizons"]["1-5d"]["evidence"]["summary"]
