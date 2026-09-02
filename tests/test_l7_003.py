from datetime import date

import pytest

from goldrush2.extractors.l7_003 import LOOKBACKS, add_yoy, build_output


def rows(count=26):
    result = []
    year, quarter = 2018, 1
    for index in range(count):
        result.append({"date": f"{year:04d}-{quarter * 3:02d}-{31 if quarter in (1, 4) else 30:02d}", "value": 100 + index * 2})
        quarter += 1
        if quarter == 5:
            quarter, year = 1, year + 1
    return result


def test_yoy_calculation():
    observations = rows(8)
    result = add_yoy(observations)
    assert result[4]["yoy_growth"] == pytest.approx(8.0)


def test_missing_prior_year_is_blank():
    assert add_yoy(rows(4))[0]["yoy_growth"] is None


@pytest.mark.parametrize("current,comparison,signal", [(30, 20, 1), (10, 20, -1), (20, 20, 0)])
def test_signal_directions(current, comparison, signal):
    observations = rows(26)
    observations[-1]["value"] = current
    observations[-5]["value"] = comparison
    # The latest quarter is also the prior-year comparison for the current
    # YoY value; set the comparison's prior-year level explicitly.
    observations[-5 - 4]["value"] = 20
    assert build_output(observations)["horizons"]["1-3y"]["signal"] == signal


@pytest.mark.parametrize("horizon", ["1-5d", "1-3m"])
def test_short_horizons_inapplicable(horizon):
    output = build_output(rows())
    assert output["horizons"][horizon]["signal"] == 0
    assert output["horizons"][horizon]["confidence"] == 1


@pytest.mark.parametrize("horizon,lookback", LOOKBACKS.items())
def test_applicable_lookbacks(horizon, lookback):
    output = build_output(rows(max(lookback + 5, 26)))
    assert output["horizons"][horizon]["confidence"] == 1


def test_high_growth_flag():
    observations = rows(26)
    observations[-1]["value"] = 200
    assert add_yoy(observations)[-1]["yoy_growth"] > 30
    assert build_output(observations)["horizons"]["1-3y"]["evidence"]["data"]["flag"] == "HIGH_GROWTH"


def test_insufficient_history():
    output = build_output(rows(5))
    assert output["horizons"]["3-10y"]["confidence"] == 0


def test_cached_degradation_note():
    output = build_output(rows(5), cached=True)
    assert "SOURCE UNAVAILABLE" in output["horizons"]["3-10y"]["evidence"]["summary"]


def test_270_day_stale_threshold():
    output = build_output(rows(), as_of_date="2025-12-31", stale_days=270)
    assert "STALE DATA" in output["horizons"]["1-3y"]["evidence"]["summary"]


def test_schema():
    output = build_output(rows())
    assert output["variable_id"] == "L7-003"
    assert set(output["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
