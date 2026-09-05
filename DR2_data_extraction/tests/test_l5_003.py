import pytest

from goldrush2.dr2.extractors.l5_003 import LOOKBACKS, build_output, quarter_rows


def rows(count=26):
    result = []
    year, quarter = 2018, 1
    for index in range(count):
        month = quarter * 3
        day = 31 if quarter == 1 or quarter == 4 else 30
        result.append({"date": f"{year:04d}-{month:02d}-{day:02d}", "value": 60 - index * 0.1})
        quarter += 1
        if quarter == 5:
            year, quarter = year + 1, 1
    return result


def test_qoq_change():
    result = quarter_rows([{"date": "2024-03-31", "value": 60}, {"date": "2024-06-30", "value": 59}])
    assert result[0]["qoq_change"] is None and result[1]["qoq_change"] == -1


@pytest.mark.parametrize("current,comparison,signal", [(58, 59, 1), (60, 59, -1), (59, 59, 0)])
def test_signal_directions(current, comparison, signal):
    observations = rows()
    observations[-1]["value"] = current
    observations[-5]["value"] = comparison
    assert build_output(observations)["horizons"]["1-3y"]["signal"] == signal


@pytest.mark.parametrize("horizon", ["1-5d", "1-3m"])
def test_short_horizons(horizon):
    output = build_output(rows())
    assert output["horizons"][horizon]["signal"] == 0 and output["horizons"][horizon]["confidence"] == 1


@pytest.mark.parametrize("horizon,lookback", LOOKBACKS.items())
def test_lookbacks(horizon, lookback):
    assert build_output(rows(max(lookback + 1, 26)))["horizons"][horizon]["confidence"] == 1


def test_large_shift_flag():
    observations = rows(6)
    observations[-1]["value"] = 70
    assert quarter_rows(observations)[-1]["flag"] == "LARGE_SHIFT"


def test_insufficient_data():
    assert build_output(rows(5))["horizons"]["3-10y"]["confidence"] == 0


def test_stale_annotation():
    output = build_output(rows(), as_of_date="2026-12-31", stale_days=200)
    assert "STALE DATA" in output["horizons"]["1-3y"]["evidence"]["summary"]


def test_cached_annotation():
    output = build_output(rows(5), cached=True)
    assert "SOURCE UNAVAILABLE" in output["horizons"]["3-10y"]["evidence"]["summary"]


def test_schema():
    output = build_output(rows())
    assert output["variable_id"] == "L5-003"
    assert set(output["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
