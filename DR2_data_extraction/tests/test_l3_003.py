from datetime import date, timedelta

from goldrush2.dr2.extractors import l3_003


def curve_rows(count=260, rate_start=4.0):
    start = date(2025, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "curve": [{"tenor": "1Y", "rate": 5}, {"tenor": "2Y", "rate": rate_start - i / 1000}], "source": "test"} for i in range(count)]


def test_metric_is_fixed_two_year():
    assert l3_003.build_output(curve_rows())["metric"] == "fixed 2Y OIS terminal proxy"


def test_uses_two_year_not_one_year():
    output = l3_003.build_output(curve_rows())
    assert output["horizons"]["1-5d"]["signal"] == 1


def test_rising_two_year_rate_is_bearish():
    data = curve_rows()
    data[-1]["curve"][1]["rate"] = 5.0
    assert l3_003.build_output(data)["horizons"]["1-5d"]["signal"] == -1


def test_unchanged_two_year_rate_is_neutral():
    data = curve_rows()
    data[-1]["curve"][1]["rate"] = data[-6]["curve"][1]["rate"]
    assert l3_003.build_output(data)["horizons"]["1-5d"]["signal"] == 0


def test_confidence_is_graded():
    horizons = l3_003.build_output(curve_rows(800))["horizons"]
    assert [horizons[k]["confidence"] for k in ("1-5d", "1-3m", "1-3y", "3-10y")] == [1.0, 0.8, 0.6, 0.4]


def test_three_to_ten_year_is_incomplete():
    result = l3_003.build_output(curve_rows(300))["horizons"]["3-10y"]
    assert result["signal"] == 0 and result["confidence"] == 0.0


def test_output_has_four_horizons():
    assert set(l3_003.build_output(curve_rows())["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}


def test_output_identifies_observation_date():
    assert l3_003.build_output(curve_rows())["observation_date"] == "2025-09-17"

