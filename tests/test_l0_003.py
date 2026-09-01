"""Tests for the L0-003 monthly ETF holdings extractor."""

from datetime import date
import io
import json
import os
import time

import pytest
from openpyxl import Workbook

from goldrush2.extractors import l0_003


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
    result = l0_003.build_output(l0_003.VARIABLE_ID, l0_003.SOURCE_NAME, l0_003.SOURCE_URL, rows, value_label="Gold ETF holdings")
    assert result["horizons"][horizon]["signal"] == signal
    assert result["horizons"][horizon]["confidence"] == 1


def test_holdings_parser(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Holdings by month"
    sheet.append(["Date", "Tonnes"])
    sheet.append([date(2026, 7, 31), 3200.5])
    path = tmp_path / "ETF_Flows_test.xlsx"
    workbook.save(path)
    assert l0_003.parse_holdings_workbook(path) == [{"date": "2026-07-31", "value": 3200.5}]


def test_insufficient_history():
    result = l0_003.build_output(l0_003.VARIABLE_ID, l0_003.SOURCE_NAME, l0_003.SOURCE_URL, observations(4), value_label="Gold ETF holdings")
    assert result["horizons"]["1-5d"]["confidence"] == 0


def test_missing_values_are_skipped(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Holdings by month"
    sheet.append(["Date", "Tonnes"])
    sheet.append(["bad", 10])
    sheet.append([date(2026, 7, 31), 3200.5])
    path = tmp_path / "ETF_Flows_test.xlsx"
    workbook.save(path)
    assert len(l0_003.parse_holdings_workbook(path)) == 1


def test_source_failure_output(monkeypatch, tmp_path):
    monkeypatch.setattr(l0_003.wgc, "fetch_wgc_workbook", lambda path: None)
    monkeypatch.setattr(l0_003.wgc, "LAST_FETCH_STALE", False)
    output = l0_003.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert output["horizons"]["1-5d"]["confidence"] == 0
    assert "SOURCE UNAVAILABLE" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_stale_output(monkeypatch, tmp_path):
    monkeypatch.setattr(l0_003.wgc, "fetch_wgc_workbook", lambda path: None)
    monkeypatch.setattr(l0_003.wgc, "LAST_FETCH_STALE", True)
    output = l0_003.run(output_path=tmp_path / "out.json", raw_dir=tmp_path)
    assert "STALE DATA" in output["horizons"]["1-5d"]["evidence"]["summary"]


def test_schema():
    result = l0_003.build_output(l0_003.VARIABLE_ID, l0_003.SOURCE_NAME, l0_003.SOURCE_URL, observations(), value_label="Gold ETF holdings")
    assert result["variable_id"] == "L0-003"
    assert result["data_frequency"] == "Monthly"
    assert set(result["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
