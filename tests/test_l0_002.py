"""Tests for the L0-002 central-bank holdings extractor."""

from datetime import datetime

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l0_002


def observations(count=756, current=200.0, comparison=100.0):
    rows = [{"date": f"{2000 + i // 12:04d}-{i % 12 + 1:02d}-28", "value": 150.0} for i in range(count)]
    if count >= 5:
        rows[-5]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(200.0, 100.0, 1), (50.0, 100.0, -1), (100.0, 100.0, 0)])
def test_directions_and_lookbacks(horizon, lookback, current, comparison, signal):
    rows = observations(current=current, comparison=100.0)
    rows[-lookback]["value"] = comparison
    result = l0_002.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def holdings_workbook(tmp_path, *, negative=False):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "PDF"
    sheet.append([None, None, None, None, None, None, None, None, None, None])
    sheet.append([None, None, "Tonnes", "% of reserves**", "Holdings as of", None, "Tonnes", "% of reserves**", "Holdings as of", None])
    sheet.append([1, "United States", -1 if negative else 8000, 0.8, datetime(2026, 6, 30), 2, "China", 2000, 0.04, datetime(2026, 6, 30)])
    path = tmp_path / "World_official_gold_holdings_test.xlsx"
    workbook.save(path)
    return path


def test_holdings_parser_and_duplicate_date_aggregation(tmp_path):
    result = l0_002.parse_holdings_workbook(holdings_workbook(tmp_path))
    assert result == [{"date": "2026-06-30", "value": 10000.0}]


def test_negative_holdings_rejected(tmp_path):
    with pytest.raises(ValueError):
        l0_002.parse_holdings_workbook(holdings_workbook(tmp_path, negative=True))


def test_insufficient_history():
    assert l0_002.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_source_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(l0_002.wgc, "fetch_wgc_official_holdings", lambda path: None)
    monkeypatch.setattr(l0_002.wgc, "LAST_FETCH_STALE", False)
    result = l0_002.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["1-5d"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in result["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(l0_002.wgc, "fetch_wgc_official_holdings", lambda path: None)
    monkeypatch.setattr(l0_002.wgc, "LAST_FETCH_STALE", True)
    result = l0_002.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert "STALE DATA" in result["horizons"]["1-5d"]["evidence"]["summary"]


def test_schema():
    result = l0_002.build_output(observations())
    assert result["variable_id"] == "L0-002"
    assert result["data_frequency"] == "Monthly"

