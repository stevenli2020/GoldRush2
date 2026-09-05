import json
from datetime import date, timedelta
from pathlib import Path

from goldrush2.dr2.collectors.ois import _checkmyswap_rows, _dtcc_seed
from goldrush2.dr2.extractors import l3_002, l3_003


def rows(count=260):
    start = date(2025, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "curve": [{"tenor": "1Y", "rate": 5 - i / 1000}, {"tenor": "2Y", "rate": 4 - i / 1000}], "source": "test"} for i in range(count)]


def test_checkmyswap_payload_normalizes_percent_rates():
    result = _checkmyswap_rows({"data": [{"date": "2026-09-02", "curve": [{"tenor": "1Y", "rate": 4.17, "trades": 10}]}]})
    assert result[0]["curve"][0]["rate"] == 4.17


def test_checkmyswap_ignores_non_year_tenors():
    result = _checkmyswap_rows({"data": [{"date": "2026-09-02", "curve": [{"tenor": "6M", "rate": 4.0}, {"tenor": "2Y", "rate": 4.2}]}]})
    assert [p["tenor"] for p in result[0]["curve"]] == ["2Y"]


def test_l3_002_uses_one_year_rate():
    output = l3_002.build_output(rows())
    assert output["metric"] == "1Y OIS rate"
    assert output["horizons"]["1-5d"]["signal"] == 1


def test_l3_003_uses_fixed_two_year_rate():
    output = l3_003.build_output(rows())
    assert output["metric"] == "fixed 2Y OIS terminal proxy"
    assert output["horizons"]["1-5d"]["signal"] == 1


def test_falling_rate_is_bullish():
    output = l3_002.build_output(rows())
    assert output["horizons"]["1-5d"]["signal"] == 1


def test_rising_rate_is_bearish():
    data = rows()
    data[-1]["curve"][0]["rate"] = 6.0
    assert l3_002.build_output(data)["horizons"]["1-5d"]["signal"] == -1


def test_three_to_ten_year_is_incomplete_without_756_observations():
    output = l3_002.build_output(rows(300))
    assert output["horizons"]["3-10y"]["signal"] == 0
    assert output["horizons"]["3-10y"]["confidence"] == 0.0


def test_l3_003_is_independent_of_l3_002_output():
    output = l3_003.build_output(rows())
    assert all("l3_002" not in key.lower() for key in json.dumps(output).split())


def test_source_boundary_does_not_create_false_signal():
    data = rows()
    data[-1]["source"] = "CheckMySwap"
    result = l3_002.build_output(data)["horizons"]["1-5d"]
    assert result["signal"] == 0 and result["confidence"] == 0.0
    assert result["evidence"]["status"] == "INCOMPLETE"
