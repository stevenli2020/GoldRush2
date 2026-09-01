"""Tests for the quarterly WGC GDT India imports extractor."""

import json

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l9_004
from goldrush2.extractors._wgc_common import quarter_end_date


def observations(count: int = 21, *, current: float = 200.0, comparison: float = 100.0) -> list[dict]:
    rows = []
    for index in range(count):
        year, quarter = 2020 + index // 4, index % 4 + 1
        net_imports = 150.0
        rows.append({"date": quarter_end_date(year, quarter), "value": net_imports, "components": {"jewellery": 80.0, "bar_coin": 40.0, "gross_imports": 180.0, "net_imports": net_imports}})
    if count > 4:
        rows[-5]["value"] = comparison
        rows[-5]["components"]["net_imports"] = comparison
    rows[-1]["value"] = current
    rows[-1]["components"]["net_imports"] = current
    return rows


def gdt_workbook(tmp_path, *, negative_component: str | None = None, missing_component: str | None = None):
    workbook = Workbook()
    balance = workbook.active
    balance.title = "Gold Balance"
    labels = [f"Q{quarter}'{year % 100:02d}" for year in range(2020, 2026) for quarter in range(1, 5)][:21]
    balance.append([None, None, None, *labels])
    balance.append([None, "Total Bar and Coin", None, *([100.0] * 21)])
    balance.append([None, "Bars", None, *([60.0] * 21)])
    balance.append([None, "Official Coins", None, *([30.0] * 21)])
    balance.append([None, "Medals Imitation Coins", None, *([10.0] * 21)])
    balance.append([None, "Recycled Gold", None, *([25.0] * 21)])

    definitions = {
        "Jewellery": ("jewellery", "India", 80.0),
        "Bar and Coin": ("bar_coin", "India", 40.0),
        "India Supply": ("gross_imports", "Gross Bullion Imports", 180.0),
    }
    for sheet_name, (component, label, value) in definitions.items():
        sheet = workbook.create_sheet(sheet_name)
        sheet.append([None, None, None, *labels])
        actual_label = f"Missing {label}" if component == missing_component else label
        values = [value] * 21
        if component == negative_component:
            values[-1] = -1.0
        sheet.append([None, actual_label, None, *values])
        if sheet_name == "India Supply":
            net_label = "Missing Net Bullion Imports" if missing_component == "net_imports" else "Net Bullion Imports"
            net_values = [150.0] * 21
            if negative_component == "net_imports":
                net_values[-1] = -1.0
            sheet.append([None, net_label, None, *net_values])
    path = tmp_path / "Gold_Demand_Trends_test.xlsx"
    workbook.save(path)
    return path


def test_parser_extracts_and_normalizes_complete_component_panel(tmp_path):
    result = l9_004.parse_india_workbook(gdt_workbook(tmp_path), cache_path=tmp_path / "parsed.json")
    assert len(result) == 21
    assert result[0]["date"] == "2020-03-31"
    assert result[-1] == {"date": "2025-03-31", "value": 150.0, "components": {"jewellery": 80.0, "bar_coin": 40.0, "gross_imports": 180.0, "net_imports": 150.0}}


@pytest.mark.parametrize("component", ["jewellery", "bar_coin", "gross_imports", "net_imports"])
def test_parser_rejects_negative_component_values(tmp_path, component):
    with pytest.raises(ValueError, match="Negative WGC GDT India"):
        l9_004.parse_india_workbook(gdt_workbook(tmp_path, negative_component=component), cache_path=None)


@pytest.mark.parametrize("component", ["jewellery", "bar_coin", "gross_imports", "net_imports"])
def test_parser_requires_every_component_row(tmp_path, component):
    with pytest.raises(ValueError, match="row or quarterly header was not found"):
        l9_004.parse_india_workbook(gdt_workbook(tmp_path, missing_component=component), cache_path=None)


@pytest.mark.parametrize("horizon,lookback", [("1-3y", 4), ("3-10y", 20)])
@pytest.mark.parametrize("current,comparison,signal", [(200.0, 100.0, 1), (50.0, 100.0, -1), (100.0, 100.0, 0)])
def test_net_import_signal_directions_and_lookbacks(horizon, lookback, current, comparison, signal):
    rows = observations(current=current)
    rows[-1 - lookback]["value"] = comparison
    rows[-1 - lookback]["components"]["net_imports"] = comparison
    result = l9_004.build_output(rows)
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1
    assert result["horizons"][horizon]["evidence"]["data"]["comparison_date"] == rows[-1 - lookback]["date"]


def test_short_horizons_are_inapplicable():
    result = l9_004.build_output(observations())
    for horizon in ("1-5d", "1-3m"):
        assert result["horizons"][horizon] == {"signal": 0, "confidence": 1, "evidence": {"summary": f"Quarterly data does not support {horizon} horizon."}}


def test_all_components_are_preserved_in_long_horizon_evidence():
    result = l9_004.build_output(observations())
    expected = {"jewellery": 80.0, "bar_coin": 40.0, "gross_imports": 180.0, "net_imports": 200.0}
    assert result["horizons"]["1-3y"]["evidence"]["data"]["components"] == expected
    assert result["horizons"]["3-10y"]["evidence"]["data"]["components"] == expected


def test_insufficient_history_preserves_current_components():
    result = l9_004.build_output(observations(4))
    assert result["horizons"]["1-3y"]["confidence"] == 0
    assert result["horizons"]["1-3y"]["evidence"]["data"]["components"]["net_imports"] == 200.0
    assert "MISSING DATA" in result["horizons"]["3-10y"]["evidence"]["summary"]


def test_cached_source_is_announced_in_valid_results():
    result = l9_004.build_output(observations(), cached=True)
    assert result["horizons"]["1-3y"]["confidence"] == 1
    assert "SOURCE UNAVAILABLE — cached data used" in result["horizons"]["1-3y"]["evidence"]["summary"]


def test_source_failure_writes_degraded_output(monkeypatch, tmp_path):
    monkeypatch.setattr(l9_004.wgc, "fetch_wgc_gdt_workbook", lambda path: None)
    monkeypatch.setattr(l9_004.wgc, "LAST_FETCH_STALE", False)
    output_path = tmp_path / "L9-004.json"
    result = l9_004.run(output_path=output_path, raw_dir=tmp_path)
    assert result["horizons"]["1-3y"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in result["horizons"]["1-3y"]["evidence"]["summary"]
    assert json.loads(output_path.read_text()) == result


def test_stale_cache_failure_is_announced(monkeypatch, tmp_path):
    monkeypatch.setattr(l9_004.wgc, "fetch_wgc_gdt_workbook", lambda path: None)
    monkeypatch.setattr(l9_004.wgc, "LAST_FETCH_STALE", True)
    result = l9_004.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["1-3y"]["confidence"] == 0
    assert "STALE DATA" in result["horizons"]["1-3y"]["evidence"]["summary"]


def test_extraction_failure_is_degraded(monkeypatch, tmp_path):
    monkeypatch.setattr(l9_004.wgc, "fetch_wgc_gdt_workbook", lambda path: tmp_path / "workbook.xlsx")
    monkeypatch.setattr(l9_004, "parse_india_workbook", lambda path: (_ for _ in ()).throw(ValueError("bad India panel")))
    result = l9_004.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert result["horizons"]["3-10y"]["confidence"] == 0
    assert "EXTRACTION FAILED — bad India panel" in result["horizons"]["3-10y"]["evidence"]["summary"]


def test_output_schema():
    result = l9_004.build_output(observations(), as_of_date="2026-09-01")
    assert result["variable_id"] == "L9-004"
    assert result["as_of_date"] == "2026-09-01"
    assert result["data_frequency"] == "Quarterly"
    assert result["source_name"] == "WGC GDT - India Net Gold Imports (consumer demand proxy)"
    assert result["observation_date"] == "2025-03-31"
    assert set(result["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
