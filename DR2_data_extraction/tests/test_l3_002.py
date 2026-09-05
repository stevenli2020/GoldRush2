from datetime import date, timedelta

from goldrush2.dr2.collectors.base import BaseCollector
from goldrush2.dr2.collectors.ois import OISCollector
from goldrush2.dr2.extractors import l3_002


def curve_rows(count=260, rate_start=5.0):
    start = date(2025, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "curve": [{"tenor": "1Y", "rate": rate_start - i / 1000}, {"tenor": "2Y", "rate": 4 - i / 1000}], "source": "test"} for i in range(count)]


def test_collector_is_base():
    assert issubclass(OISCollector, BaseCollector)


def test_metric_is_one_year():
    assert l3_002.build_output(curve_rows())["metric"] == "1Y OIS rate"


def test_falling_rate_is_bullish():
    assert l3_002.build_output(curve_rows())["horizons"]["1-5d"]["signal"] == 1


def test_rising_rate_is_bearish():
    data = curve_rows()
    data[-1]["curve"][0]["rate"] = 6.0
    assert l3_002.build_output(data)["horizons"]["1-5d"]["signal"] == -1


def test_unchanged_rate_is_neutral():
    data = curve_rows()
    data[-1]["curve"][0]["rate"] = data[-6]["curve"][0]["rate"]
    assert l3_002.build_output(data)["horizons"]["1-5d"]["signal"] == 0


def test_confidence_is_graded():
    horizons = l3_002.build_output(curve_rows(800))["horizons"]
    assert [horizons[k]["confidence"] for k in ("1-5d", "1-3m", "1-3y", "3-10y")] == [1.0, 0.8, 0.6, 0.4]


def test_three_to_ten_year_is_incomplete_without_756_observations():
    result = l3_002.build_output(curve_rows(300))["horizons"]["3-10y"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_output_has_four_horizons():
    assert set(l3_002.build_output(curve_rows())["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}


def test_output_identifies_observation_date():
    assert l3_002.build_output(curve_rows())["observation_date"] == "2025-09-17"

