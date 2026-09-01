"""Tests for the L5-006 official-sector net-reduction extractor."""

from datetime import datetime

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l5_006


def observations(count=756, current=20.0, comparison=10.0):
    rows = [{"date": f"{2000 + i // 12:04d}-{i % 12 + 1:02d}-28", "value": 15.0} for i in range(count)]
    if count >= 5:
        rows[-5]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(20.0, 10.0, -1), (5.0, 10.0, 1), (10.0, 10.0, 0)])
def test_directions_and_lookbacks(horizon, lookback, current, comparison, signal):
    rows = observations(current=current, comparison=10.0)
    rows[-lookback]["value"] = comparison
    result = l5_006.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def test_parser_keeps_negative_canonical_changes_and_converts_to_positive(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Monthly"
    sheet.append([None, "Country", None, datetime(2026, 6, 30), datetime(2026, 7, 31)])
    sheet.append([None, "US", None, -2.0, 1.0])
    sheet.append([None, "Turkey*", None, -100.0, -100.0])
    sheet.append([None, "Turkey", None, -3.0, -0.00001])
    path = tmp_path / "Changes_latest_as_of_test_IFS.xlsx"
    workbook.save(path)
    assert l5_006.parse_reductions_workbook(path) == [{"date": "2026-06-30", "value": 5.0}]


def test_insufficient_history():
    assert l5_006.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_schema_and_proxy_label():
    result = l5_006.build_output(observations())
    assert result["variable_id"] == "L5-006"
    assert "proxy" in result["source_name"]
    assert result["data_frequency"] == "Monthly"


def test_source_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(l5_006.wgc, "fetch_wgc_official_changes", lambda path: None)
    monkeypatch.setattr(l5_006.wgc, "LAST_FETCH_STALE", False)
    result = l5_006.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["1-5d"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in result["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(l5_006.wgc, "fetch_wgc_official_changes", lambda path: None)
    monkeypatch.setattr(l5_006.wgc, "LAST_FETCH_STALE", True)
    result = l5_006.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert "STALE DATA" in result["horizons"]["1-5d"]["evidence"]["summary"]

