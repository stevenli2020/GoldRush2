import json
import math
import os
from datetime import date, timedelta

import pytest

from goldrush2.extractors import l1_001, l1_002, l1_007


def make_observations(count=756, value=2.0):
    start = date(2024, 1, 1)
    return [
        {"date": (start + timedelta(days=index)).isoformat(), "value": value}
        for index in range(count)
    ]


def raw_payload(observations):
    return {
        "observations": [
            {"date": observation["date"], "value": str(observation["value"])}
            for observation in observations
        ]
    }


def current_output(variable_id, observations, *, cached=False, confidence=1):
    latest = observations[-1]
    suffix = " SOURCE UNAVAILABLE — cached data used." if cached else ""
    return {
        "variable_id": variable_id,
        "horizons": {
            horizon: {
                "signal": 0,
                "confidence": confidence,
                "evidence": {
                    "data": {
                        "current_value": latest["value"],
                        "current_date": latest["date"],
                    },
                    "summary": "Available" + suffix,
                },
            }
            for horizon in ("1-5d", "1-3m", "1-3y", "3-10y")
        },
    }


def write_dependencies(tmp_path, observations10, observations5, *, cached=False, confidence=1):
    raw10 = tmp_path / "DFII10.json"
    raw5 = tmp_path / "DFII5.json"
    output10 = tmp_path / "L1-001.json"
    output5 = tmp_path / "L1-002.json"
    raw10.write_text(json.dumps(raw_payload(observations10)), encoding="utf-8")
    raw5.write_text(json.dumps(raw_payload(observations5)), encoding="utf-8")
    output10.write_text(json.dumps(current_output("L1-001", observations10, cached=cached, confidence=confidence)), encoding="utf-8")
    output5.write_text(json.dumps(current_output("L1-002", observations5, cached=cached, confidence=confidence)), encoding="utf-8")
    return raw10, raw5, output10, output5


def patch_dependency_paths(monkeypatch, paths):
    raw10, raw5, output10, output5 = paths
    monkeypatch.setattr(l1_001, "RAW_PATH", raw10)
    monkeypatch.setattr(l1_002, "RAW_PATH", raw5)
    monkeypatch.setattr(l1_001, "OUTPUT_PATH", output10)
    monkeypatch.setattr(l1_002, "OUTPUT_PATH", output5)


def test_forward_rate_formula_known_inputs():
    result = l1_007._forward_rate(2.34, 2.10)

    expected = ((((1 + 2.34 / 100) ** 10 / (1 + 2.10 / 100) ** 5) ** (1 / 5)) - 1) * 100
    assert result == pytest.approx(expected)
    assert result == pytest.approx(2.58, abs=0.01)


def test_forward_rate_equals_spot_when_real_yields_are_equal():
    assert l1_007._forward_rate(2.1, 2.1) == pytest.approx(2.1)


def test_forward_rate_handles_extreme_valid_values():
    result = l1_007._forward_rate(50.0, -50.0)

    assert math.isfinite(result)


def test_forward_rate_rejects_nonfinite_and_out_of_domain_values():
    with pytest.raises(l1_007.DependencyError):
        l1_007._forward_rate(float("nan"), 2.0)
    with pytest.raises(l1_007.DependencyError):
        l1_007._forward_rate(-100.0, 2.0)


def test_build_output_has_all_four_signal_horizons_and_formula():
    observations10 = make_observations(value=2.0)
    observations5 = make_observations(value=2.0)
    observations10[-5]["value"] = 2.1
    observations5[-63]["value"] = 2.1
    observations10[-756]["value"] = 2.1

    output = l1_007.build_output(observations10, observations5, as_of_date="2026-09-01")

    assert output["horizons"]["1-5d"]["signal"] == 1
    assert output["horizons"]["1-3m"]["signal"] == -1
    assert output["horizons"]["1-3y"]["signal"] == 0
    assert output["horizons"]["3-10y"]["signal"] == 1
    assert output["horizons"]["1-5d"]["confidence"] == 1
    assert output["calculation_formula"] == l1_007.CALCULATION_FORMULA


@pytest.mark.parametrize("invalid_value", [None, float("nan")])
def test_missing_or_nonfinite_dependency_returns_zero_confidence_for_all_horizons(
    monkeypatch, tmp_path, invalid_value
):
    observations10 = make_observations()
    observations5 = make_observations()
    paths = write_dependencies(tmp_path, observations10, observations5)
    patch_dependency_paths(monkeypatch, paths)
    invalid_output = current_output("L1-001", observations10)
    invalid_output["horizons"]["1-5d"]["evidence"]["data"]["current_value"] = invalid_value
    paths[2].write_text(json.dumps(invalid_output), encoding="utf-8")

    output = l1_007.run(output_path=tmp_path / "L1-007.json")

    for result in output["horizons"].values():
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("DEPENDENCY FAILED")


def test_zero_confidence_dependency_returns_zero_confidence_for_all_horizons(monkeypatch, tmp_path):
    observations10 = make_observations()
    observations5 = make_observations()
    paths = write_dependencies(tmp_path, observations10, observations5)
    patch_dependency_paths(monkeypatch, paths)
    invalid_output = current_output("L1-001", observations10, confidence=0)
    paths[2].write_text(json.dumps(invalid_output), encoding="utf-8")

    output = l1_007.run(output_path=tmp_path / "L1-007.json")

    assert all(result["confidence"] == 0 for result in output["horizons"].values())


def test_stale_dependency_returns_stale_dependent_data(monkeypatch, tmp_path):
    observations = make_observations()
    paths = write_dependencies(tmp_path, observations, observations)
    patch_dependency_paths(monkeypatch, paths)
    now = 1_000_000.0
    monkeypatch.setattr(l1_007.time, "time", lambda: now)
    os.utime(paths[0], (now - 7 * 86400, now - 7 * 86400))

    output = l1_007.run(output_path=tmp_path / "L1-007.json")

    for result in output["horizons"].values():
        assert result["signal"] == 0
        assert result["confidence"] == 0
        assert result["evidence"]["summary"].startswith("STALE DEPENDENT DATA")


def test_cached_dependencies_are_used_and_annotated(monkeypatch, tmp_path, capsys):
    observations = make_observations()
    paths = write_dependencies(tmp_path, observations, observations, cached=True)
    patch_dependency_paths(monkeypatch, paths)

    output = l1_007.run(output_path=tmp_path / "L1-007.json")

    assert capsys.readouterr().out.strip() == "DEPENDENT SOURCE UNAVAILABLE — cached data used"
    for horizon in output["horizons"].values():
        assert horizon["confidence"] == 1
        assert "DEPENDENT SOURCE UNAVAILABLE — cached data used" in horizon["evidence"]["summary"]


def test_missing_dependency_file_returns_zero_confidence(monkeypatch, tmp_path):
    observations = make_observations()
    paths = write_dependencies(tmp_path, observations, observations)
    patch_dependency_paths(monkeypatch, paths)
    paths[1].unlink()

    output = l1_007.run(output_path=tmp_path / "L1-007.json")

    assert all(result["confidence"] == 0 for result in output["horizons"].values())
