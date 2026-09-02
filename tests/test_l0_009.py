from datetime import date, timedelta
import json

import pytest

from goldrush2.extractors.l0_009 import LOOKBACKS, build_output, run


def observations(count=757, *, value_step=0.01):
    start = date(2023, 1, 2)
    return [
        {
            "date": (start + timedelta(days=index)).isoformat(),
            "value": round(index * value_step, 8),
            "forward_rate": 4.5,
            "sofr": 4.0,
            "near_contract": "GCV26.CMX",
            "far_contract": "GCZ26.CMX",
            "days_between": 61,
            "sofr_is_filled": False,
        }
        for index in range(count)
    ]


def test_forward_lease_proxy_signal_rises():
    assert build_output(observations())["horizons"]["1-5d"]["signal"] == 1


def test_forward_lease_proxy_signal_falls():
    assert build_output(observations(value_step=-0.01))["horizons"]["1-5d"]["signal"] == -1


def test_forward_lease_proxy_signal_is_neutral_when_unchanged():
    rows = observations(6, value_step=0.0)
    result = build_output(rows)["horizons"]["1-5d"]
    assert result["signal"] == 0
    assert result["confidence"] == 1.0


@pytest.mark.parametrize("horizon,lookback", LOOKBACKS.items())
def test_all_horizon_lookbacks(horizon, lookback):
    result = build_output(observations())["horizons"][horizon]
    assert result["evidence"]["data"]["comparison_date"] == observations()[-1 - lookback]["date"]


def test_insufficient_data_returns_zero_confidence():
    result = build_output(observations(252))["horizons"]["3-10y"]
    assert result["signal"] == 0
    assert result["confidence"] == 0.0


def test_short_horizon_requires_six_observations():
    result = build_output(observations(5))["horizons"]["1-5d"]
    assert result["signal"] == 0
    assert result["confidence"] == 0.0


def test_evidence_contains_components_and_change():
    data = build_output(observations())["horizons"]["1-5d"]["evidence"]["data"]
    assert {"current_value", "comparison_value", "change_pp", "forward_rate", "sofr", "near_contract", "far_contract", "days_between"} <= set(data)


def test_sofr_fill_flag_is_preserved():
    rows = observations(6)
    rows[-1]["sofr_is_filled"] = True
    assert build_output(rows)["horizons"]["1-5d"]["evidence"]["data"]["sofr_is_filled"] is True


def test_output_schema():
    output = build_output(observations())
    assert output["variable_id"] == "L0-009"
    assert output["data_frequency"] == "Daily"
    assert set(output["horizons"]) == set(LOOKBACKS)


def test_valid_horizon_confidence_is_one():
    assert build_output(observations())["horizons"]["1-3y"]["confidence"] == 1.0


def test_run_writes_current_output(tmp_path):
    cache_path = tmp_path / "cache.json"
    output_path = tmp_path / "current.json"
    cache_path.write_text(json.dumps(observations(6)), encoding="utf-8")
    assert run(cache_path=cache_path, output_path=output_path)["variable_id"] == "L0-009"
    assert output_path.exists()
