import json
import shutil

import pytest

from goldrush2.dr3.analytics.multi_strategy import StrategyValidationError, _current_signal, _validate_weights, load_strategy_set, run_multi_strategy
from goldrush2.paths import DR3_STRATEGIES_DIR


def test_strategy_set_contains_the_frozen_fifteen_configs():
    strategies = load_strategy_set()
    assert len(strategies) == 15
    assert [item["config"]["strategy"]["id"] for item in strategies][-1] == "SP-ALL"
    short = next(item["config"] for item in strategies if item["config"]["strategy"]["id"] == "SP-SHORT")
    assert short["horizon_weights"]["1-3y"]["L8-001"] == 0.25


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        ("L1-001: 0.61", "weights sum"),
        ("L1-001", "unknown variables"),
    ],
)
def test_invalid_strategy_config_hard_fails(tmp_path, replacement, message):
    strategies_dir = tmp_path / "strategies"
    shutil.copytree(DR3_STRATEGIES_DIR, strategies_dir)
    rate_path = strategies_dir / "weights_strategy_SP-RATE.yaml"
    text = rate_path.read_text(encoding="utf-8")
    if replacement == "L1-001: 0.61":
        text = text.replace("L1-001: 0.60", replacement)
    else:
        text = text.replace("L1-001", "L99-999")
    rate_path.write_text(text, encoding="utf-8")
    with pytest.raises(StrategyValidationError, match=message):
        load_strategy_set(strategies_dir)


def test_missing_horizon_hard_fails(tmp_path):
    strategies_dir = tmp_path / "strategies"
    shutil.copytree(DR3_STRATEGIES_DIR, strategies_dir)
    rate_path = strategies_dir / "weights_strategy_SP-RATE.yaml"
    text = rate_path.read_text(encoding="utf-8").replace("  3-10y: *rate\n", "")
    rate_path.write_text(text, encoding="utf-8")
    with pytest.raises(StrategyValidationError, match="horizon weights"):
        load_strategy_set(strategies_dir)


def test_negative_weight_and_excess_active_variables_hard_fail():
    known = {f"L0-{index:03d}" for index in range(1, 18)}
    weights = {horizon: {"L0-001": 1.0} for horizon in ("1-5d", "1-3m", "1-3y", "3-10y")}
    weights["1-5d"]["L0-001"] = -0.1
    with pytest.raises(StrategyValidationError, match="negative"):
        _validate_weights(weights, "TEST", known, 0.001, 15)

    weights["1-5d"] = {f"L0-{index:03d}": 1 / 16 for index in range(1, 17)}
    with pytest.raises(StrategyValidationError, match="exceeds 15"):
        _validate_weights(weights, "TEST", known, 0.001, 15)


def test_missing_current_signal_is_neutral_without_weight_renormalization():
    assert _current_signal({}, "L1-001", "1-5d") == 0


def test_multi_strategy_output_is_current_only_and_non_official(tmp_path):
    output_path = tmp_path / "dr3_multi_strategy_outlook.json"
    result = run_multi_strategy(output_path=output_path)
    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert result == persisted
    assert result["mode"] == "current_outlook_only"
    assert result["official_strategy"] is None
    assert result["admit_variable_count"] == 45
    assert len(result["strategies"]) == 15
    assert set(result["strategies"]["SP-RATE"]["horizons"]) == {"1-5d", "1-3m", "1-3y", "3-10y"}
    assert result["strategies"]["SP-TECH"]["production_eligible"] is False
    assert result["strategies"]["SP-ALL"]["production_eligible"] is False
    assert result["strategies"]["SP-ALL"]["horizons"]["1-5d"]["active_variables"] == "AUTO_UNIFORM_ADMIT"
