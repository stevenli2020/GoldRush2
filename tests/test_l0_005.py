"""Tests for the quarterly WGC GDT bar-and-coin extractor."""

from datetime import date

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l0_005


def observations(count=21, current=200.0, comparison=100.0):
    rows = [{"date": f"{2020 + i // 4:04d}-{(i % 4 + 1) * 3:02d}-30", "value": 150.0} for i in range(count)]
    if count > 4:
        rows[-1 - 4]["value"] = comparison
    rows[-1]["value"] = current
    return rows


@pytest.mark.parametrize("horizon, lookback", [("1-3y", 4), ("3-10y", 20)])
@pytest.mark.parametrize("current, comparison, signal", [(200.0, 100.0, 1), (50.0, 100.0, -1), (100.0, 100.0, 0)])
def test_signal_directions_and_lookbacks(horizon, lookback, current, comparison, signal):
    rows = observations(current=current)
    rows[-1 - lookback]["value"] = comparison
    result = l0_005.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def test_short_horizons_are_inapplicable():
    result = l0_005.build_output(observations())
    for horizon in ("1-5d", "1-3m"):
        assert result["horizons"][horizon]["signal"] == 0
        assert result["horizons"][horizon]["confidence"] == 1
        assert "does not support" in result["horizons"][horizon]["evidence"]["summary"]


def gdt_workbook(tmp_path, *, bad_components=False):
    workbook = Workbook()
    balance = workbook.active
    balance.title = "Gold Balance"
    for _ in range(4):
        balance.append([])
    balance.append([None, None, None, "Q1 2025", "Q2 2025"])
    total = 102.0 if bad_components else 100.0
    balance.append([None, "Total Bar and Coin", None, 100.0, total])
    balance.append([None, "Bars", None, 60.0, 60.0])
    balance.append([None, "Official Coins", None, 30.0, 30.0])
    balance.append([None, "Medals Imitation Coins", None, 10.0, 10.0])
    balance.append([None, "Recycled Gold", None, 25.0, 26.0])
    path = tmp_path / "GDT_Tables_Q1'25_EN.xlsx"
    workbook.save(path)
    return path


def test_parser_normalizes_quarters_and_reconciles_components(tmp_path):
    result = l0_005.parse_demand_workbook(gdt_workbook(tmp_path), cache_path=tmp_path / "parsed.json")
    assert result == [{"date": "2025-03-31", "value": 100.0, "bars": 60.0, "official_coins": 30.0, "medals_imitation_coins": 10.0}, {"date": "2025-06-30", "value": 100.0, "bars": 60.0, "official_coins": 30.0, "medals_imitation_coins": 10.0}]


def test_component_reconciliation_failure(tmp_path):
    with pytest.raises(ValueError, match="do not reconcile"):
        l0_005.parse_demand_workbook(gdt_workbook(tmp_path, bad_components=True), cache_path=None)


def test_parser_cache_reuse(tmp_path, monkeypatch):
    workbook = gdt_workbook(tmp_path)
    cache = tmp_path / "parsed.json"
    expected = l0_005.parse_demand_workbook(workbook, cache_path=cache)
    monkeypatch.setattr("goldrush2.extractors._wgc_common.load_workbook", lambda *args: (_ for _ in ()).throw(AssertionError("reparsed")), raising=False)
    assert l0_005.parse_demand_workbook(workbook, cache_path=cache) == expected


def test_insufficient_history():
    assert l0_005.build_output(observations(4))["horizons"]["1-3y"]["confidence"] == 0


def test_schema():
    result = l0_005.build_output(observations())
    assert result["variable_id"] == "L0-005"
    assert result["data_frequency"] == "Quarterly"
    assert set(result["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}


def test_source_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(l0_005.wgc, "fetch_wgc_gdt_workbook", lambda path: None)
    monkeypatch.setattr(l0_005.wgc, "LAST_FETCH_STALE", False)
    result = l0_005.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["1-3y"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in result["horizons"]["1-3y"]["evidence"]["summary"]


def test_stale_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(l0_005.wgc, "fetch_wgc_gdt_workbook", lambda path: None)
    monkeypatch.setattr(l0_005.wgc, "LAST_FETCH_STALE", True)
    result = l0_005.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert "STALE DATA" in result["horizons"]["1-3y"]["evidence"]["summary"]
