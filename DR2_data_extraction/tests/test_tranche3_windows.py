from goldrush2.dr2.extractors import l8_001
from goldrush2.dr2.extractors._wgc_common import build_quarterly_output


def monthly_rows(count):
    return [{"date": f"{2000 + i // 12:04d}-{i % 12 + 1:02d}-28", "value": float(i)} for i in range(count)]


def quarterly_rows(count):
    return [{"date": f"{2000 + i // 4:04d}-{(i % 4) * 3 + 3:02d}-28", "value": float(i)} for i in range(count)]


def test_monthly_boundaries_36_and_120():
    below_36 = l8_001.build_output(l8_001.VARIABLE_ID, l8_001.SOURCE_NAME, l8_001.SOURCE_URL, monthly_rows(35), as_of_date="2100-01-01")
    at_36 = l8_001.build_output(l8_001.VARIABLE_ID, l8_001.SOURCE_NAME, l8_001.SOURCE_URL, monthly_rows(36), as_of_date="2100-01-01")
    below_120 = l8_001.build_output(l8_001.VARIABLE_ID, l8_001.SOURCE_NAME, l8_001.SOURCE_URL, monthly_rows(119), as_of_date="2100-01-01")
    at_120 = l8_001.build_output(l8_001.VARIABLE_ID, l8_001.SOURCE_NAME, l8_001.SOURCE_URL, monthly_rows(120), as_of_date="2100-01-01")
    assert below_36["horizons"]["1-3y"]["confidence"] == 0
    assert at_36["horizons"]["1-3y"]["confidence"] == 1
    assert below_120["horizons"]["3-10y"]["confidence"] == 0
    assert at_120["horizons"]["3-10y"]["confidence"] == 1


def test_quarterly_boundaries_12_and_40():
    def build(rows):
        return build_quarterly_output("TEST", "test", "https://example.test", rows, value_label="test", rising_signal=1, falling_signal=-1, as_of_date="2100-01-01")
    assert build(quarterly_rows(11))["horizons"]["1-3y"]["confidence"] == 0
    assert build(quarterly_rows(12))["horizons"]["1-3y"]["confidence"] == 1
    assert build(quarterly_rows(39))["horizons"]["3-10y"]["confidence"] == 0
    assert build(quarterly_rows(40))["horizons"]["3-10y"]["confidence"] == 1
