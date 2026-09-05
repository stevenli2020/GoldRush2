"""Expert-reviewed tests for DR3 aggregation engine."""
import json
import subprocess
from pathlib import Path
import pytest
import yaml
from goldrush2.dr3.analytics.aggregator import aggregate_horizon, load_weights, run_analytics
from goldrush2.dr3.analytics.models import VariableResult, HorizonSignal, Evidence, EvidenceData
from goldrush2.paths import DR3_CONFIG_DIR

def make_var(var_id, signal=1, conf=1.0, summary="Test", applicable=None):
    data = {} if applicable is None else {"applicable": applicable}
    return {"variable_id": var_id, "as_of_date": "2026-09-01", "sources": [], 
            "horizons": {"1-5d": {"signal": signal, "confidence": conf, "evidence": {"data": data, "summary": summary}}}}

def test_yaml_syntax_and_coverage():
    config = load_weights(DR3_CONFIG_DIR / "weights_v1.yaml")
    assert "horizons" in config
    assert "L5-002" not in (DR3_CONFIG_DIR / "weights_v1.yaml").read_text(encoding="utf-8")
    for hz in config["horizons"].values():
        assert "L5-002" not in hz
        assert len(hz) >= 30

def test_structural_omission_before_normalization():
    # If a variable is structurally inapplicable, it shouldn't dilute the score
    raw_weights = {"L1-001": 10, "L4-006": 10}
    variables = {
        "L1-001": VariableResult.from_dict(make_var("L1-001", signal=1, conf=1.0)),
        "L4-006": VariableResult.from_dict(make_var("L4-006", signal=0, conf=1.0, summary="Quarterly data is unavailable for this horizon.", applicable=False))
    }
    score, _ = aggregate_horizon("1-5d", raw_weights, variables)
    # L4-006 should be omitted. L1-001 is the only applicable variable, so score should be +100
    assert score.score == 100
    assert score.data_availability == 1.0

def test_confidence_weighted_denominator():
    # Formula: sum(S*W*C) / sum(W*C)
    # If both variables have C=0.5 and S=1, raw_score should still be 1.0 (+100)
    raw_weights = {"L1-001": 10, "L1-002": 10}
    variables = {
        "L1-001": VariableResult.from_dict(make_var("L1-001", signal=1, conf=0.5)),
        "L1-002": VariableResult.from_dict(make_var("L1-002", signal=1, conf=0.5))
    }
    score, _ = aggregate_horizon("1-5d", raw_weights, variables)
    assert score.score == 100
    assert score.confidence == 0.5

def test_degraded_status_threshold():
    raw_weights = {"L1-001": 8, "L1-002": 2}
    variables = {
        "L1-001": VariableResult.from_dict(make_var("L1-001", signal=1, conf=0.0)), # Missing
        "L1-002": VariableResult.from_dict(make_var("L1-002", signal=1, conf=1.0))
    }
    score, warnings = aggregate_horizon("1-5d", raw_weights, variables)
    # Availability is 0.2 (20%). Should be DEGRADED.
    assert score.status == "DEGRADED"
    assert score.data_availability == pytest.approx(0.2, abs=0.01)

def test_missing_variable_reduces_availability():
    score, _ = aggregate_horizon("1-5d", {"L1-001": 1, "L1-002": 1}, {
        "L1-001": VariableResult.from_dict(make_var("L1-001", signal=1, conf=1.0))
    })
    assert score.data_availability == pytest.approx(0.5)
    assert score.status == "DEGRADED"

def test_explicit_applicability_false_is_excluded():
    score, _ = aggregate_horizon("1-5d", {"L1-001": 1, "L1-002": 1}, {
        "L1-001": VariableResult.from_dict(make_var("L1-001", signal=1, conf=1.0)),
        "L1-002": VariableResult.from_dict(make_var("L1-002", signal=-1, conf=1.0, applicable=False)),
    })
    assert score.score == 100
    assert score.data_availability == pytest.approx(1.0)

def test_top_five_warning_uses_normalized_configured_weights():
    score, warnings = aggregate_horizon("1-5d", {"L1-001": 10, "L1-002": 1}, {
        "L1-002": VariableResult.from_dict(make_var("L1-002", signal=1, conf=1.0))
    })
    assert score.status == "DEGRADED"
    assert any("HIGH_WEIGHT_MISSING: L1-001" in warning for warning in warnings)

def test_cli_analyze_command():
    # End-to-end test
    result = subprocess.run(["gr2", "analyze"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "GoldRush2" in result.stdout or "DR3" in result.stdout
