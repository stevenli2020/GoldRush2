from datetime import date

import pytest

from goldrush2.dr2.extractors import l1_006


def _rows():
    return [
        {"contract": "ZQQ26", "settlement_price": 96.00, "expiry_date": "2026-08-31", "implied_rate": 4.00},
        {"contract": "ZQU26", "settlement_price": 96.00, "expiry_date": "2026-09-30", "implied_rate": 4.00},
        {"contract": "ZQZ26", "settlement_price": 96.00, "expiry_date": "2026-12-31", "implied_rate": 4.00},
        {"contract": "ZQZ27", "settlement_price": 96.00, "expiry_date": "2027-12-31", "implied_rate": 4.00},
    ]


def _dff(value=3.75):
    return [{"date": "2026-08-20", "value": value}]


def _tarmd(value=3.10):
    return [{"date": "2026-06-15", "value": value}]


def test_contract_selection_and_threshold_directions():
    observation = date(2026, 8, 20)
    contract, target = l1_006.select_contract(_rows(), "1-3m", observation)
    assert contract["contract"] == "ZQZ26"
    assert target == date(2026, 11, 20)
    current = {"date": "2026-08-20", "value": 3.75}
    assert l1_006._short_result({**contract, "implied_rate": 4.0}, current, target, cached=False)["signal"] == -1
    assert l1_006._short_result({**contract, "implied_rate": 3.60}, current, target, cached=False)["signal"] == 1
    assert l1_006._short_result({**contract, "implied_rate": 3.80}, current, target, cached=False)["signal"] == 0


def test_build_output_includes_all_horizons_and_annual_fallback_label():
    output = l1_006.build_output(_rows(), date(2026, 8, 20), _dff(), _tarmd())
    assert set(output["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
    long_summary = output["horizons"]["3-10y"]["evidence"]["summary"]
    assert "annual SEP projection" in long_summary
    assert "2026-06-15" in long_summary
    assert "target_date" in output["horizons"]["1-3m"]["evidence"]["data"]


def test_missing_contract_is_degraded():
    with pytest.raises(l1_006.DependencyError):
        l1_006.select_contract([], "1-5d", date(2026, 8, 20))


def test_degraded_output_has_zero_confidence():
    output = l1_006.build_degraded_output("STALE DATA")
    assert all(item["signal"] == 0 and item["confidence"] == 0 for item in output["horizons"].values())
