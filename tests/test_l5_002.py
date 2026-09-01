"""Tests for the L5-002 official-reserve-share extractor."""

from datetime import datetime

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l5_002


def observations(count=756, current=0.2, comparison=0.1):
    rows = [{"date": f"{2000 + i // 12:04d}-{i % 12 + 1:02d}-28", "value": 0.15} for i in range(count)]
    if count >= 5:
        rows[-5]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-5d", 5), ("1-3m", 63), ("1-3y", 252), ("3-10y", 756)])
@pytest.mark.parametrize("current, comparison, signal", [(0.2, 0.1, 1), (0.05, 0.1, -1), (0.1, 0.1, 0)])
def test_directions_and_lookbacks(horizon, lookback, current, comparison, signal):
    rows = observations(current=current, comparison=0.1)
    rows[-lookback]["value"] = comparison
    result = l5_002.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def share_workbook(tmp_path, *, invalid=False):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "PDF"
    sheet.append([None, None, None, None, None, None, None, None, None, None])
    sheet.append([None, None, "Tonnes", "% of reserves**", "Holdings as of", None, "Tonnes", "% of reserves**", "Holdings as of", None])
    sheet.append([1, "United States", 8000, 1.2 if invalid else 0.8, datetime(2026, 6, 30), 2, "China", 2000, 0.4, datetime(2026, 6, 30)])
    sheet.append([3, "Total", 10000, 0.9, datetime(2026, 6, 30), None, None, None, None, None])
    path = tmp_path / "World_official_gold_holdings_test.xlsx"
    workbook.save(path)
    return path


def test_two_panel_parser_and_aggregate_exclusion(tmp_path):
    result = l5_002.parse_reserve_share_workbook(share_workbook(tmp_path))
    assert result == [{"date": "2026-06-30", "value": 0.6}]


def test_out_of_range_share_rejected_from_valid_records(tmp_path):
    with pytest.raises(ValueError):
        l5_002.parse_reserve_share_workbook(share_workbook(tmp_path, invalid=True))


def test_insufficient_history():
    assert l5_002.build_output(observations(4))["horizons"]["1-5d"]["confidence"] == 0


def test_source_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(l5_002.wgc, "fetch_wgc_official_holdings", lambda path: None)
    monkeypatch.setattr(l5_002.wgc, "LAST_FETCH_STALE", False)
    result = l5_002.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["1-5d"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in result["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(l5_002.wgc, "fetch_wgc_official_holdings", lambda path: None)
    monkeypatch.setattr(l5_002.wgc, "LAST_FETCH_STALE", True)
    result = l5_002.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert "STALE DATA" in result["horizons"]["1-5d"]["evidence"]["summary"]


def test_schema():
    result = l5_002.build_output(observations())
    assert result["variable_id"] == "L5-002"
    assert result["data_frequency"] == "Monthly"
