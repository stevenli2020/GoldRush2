"""Current-outlook comparison of immutable DR3 sparse strategies."""
from __future__ import annotations

import importlib
import json
import pkgutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from goldrush2.dr3.analytics.aggregator import HORIZONS, load_variable_results
from goldrush2.paths import DR3_MULTI_STRATEGY_OUTPUT_PATH, DR3_STRATEGIES_DIR


class StrategyValidationError(ValueError):
    """Raised when an immutable strategy configuration is not valid."""


def production_variable_ids() -> set[str]:
    """Return the current GR2 production variable registry from extractor modules."""
    package = importlib.import_module("goldrush2.dr2.extractors")
    return {
        module.name.upper().replace("_", "-")
        for module in pkgutil.iter_modules(package.__path__)
        if module.name.startswith("l") and module.name[1:].replace("_", "").isdigit()
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise StrategyValidationError(f"Cannot load strategy configuration: {path}") from exc
    if not isinstance(payload, dict):
        raise StrategyValidationError(f"Strategy configuration must be a mapping: {path}")
    return payload


def _validate_weights(weights: dict[str, Any], strategy_id: str, known_ids: set[str], tolerance: float, max_variables: int) -> None:
    if set(weights) != set(HORIZONS):
        raise StrategyValidationError(f"{strategy_id}: horizon weights must contain exactly {HORIZONS}")
    for horizon, horizon_weights in weights.items():
        if not isinstance(horizon_weights, dict) or not horizon_weights:
            raise StrategyValidationError(f"{strategy_id}: {horizon} must contain variable weights")
        if set(horizon_weights) - known_ids:
            unknown = sorted(set(horizon_weights) - known_ids)
            raise StrategyValidationError(f"{strategy_id}: {horizon} has unknown variables: {', '.join(unknown)}")
        try:
            values = [float(weight) for weight in horizon_weights.values()]
        except (TypeError, ValueError) as exc:
            raise StrategyValidationError(f"{strategy_id}: {horizon} weights must be numeric") from exc
        if any(weight < 0 for weight in values):
            raise StrategyValidationError(f"{strategy_id}: {horizon} has a negative weight")
        if sum(weight > 0 for weight in values) > max_variables:
            raise StrategyValidationError(f"{strategy_id}: {horizon} exceeds {max_variables} active variables")
        if abs(sum(values) - 1.0) > tolerance:
            raise StrategyValidationError(f"{strategy_id}: {horizon} weights sum to {sum(values):.6f}, not 1.0")


def load_strategy_set(strategies_dir: Path = DR3_STRATEGIES_DIR, known_ids: set[str] | None = None) -> list[dict[str, Any]]:
    """Load and hard-validate every configuration listed in ``strategies.yaml``."""
    registry = known_ids or production_variable_ids()
    index = _load_yaml(strategies_dir / "strategies.yaml")
    entries = index.get("strategies")
    if not isinstance(entries, list) or len(entries) != 15:
        raise StrategyValidationError("strategies.yaml must list exactly 15 strategies")

    loaded: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not isinstance(entry.get("file"), str):
            raise StrategyValidationError("Every strategy index entry needs an id and file")
        config = _load_yaml(strategies_dir / entry["file"])
        strategy = config.get("strategy")
        validation = config.get("validation")
        if not isinstance(strategy, dict) or strategy.get("id") != entry["id"]:
            raise StrategyValidationError(f"{entry['id']}: strategy id does not match its index entry")
        if strategy["id"] in seen_ids:
            raise StrategyValidationError(f"Duplicate strategy id: {strategy['id']}")
        seen_ids.add(strategy["id"])
        if strategy.get("frozen") is not True:
            raise StrategyValidationError(f"{strategy['id']}: frozen must be true")
        if not isinstance(validation, dict):
            raise StrategyValidationError(f"{strategy['id']}: validation is required")

        if strategy["id"] == "SP-ALL":
            if config.get("horizon_weights") != "AUTO_UNIFORM_ADMIT" or validation.get("exempt_from_max_variables") is not True:
                raise StrategyValidationError("SP-ALL must use AUTO_UNIFORM_ADMIT and be exempt from max variables")
        else:
            tolerance = float(validation.get("sum_tolerance", 0.001))
            max_variables = validation.get("max_variables")
            if max_variables != 15 or validation.get("exempt_from_max_variables") is not False:
                raise StrategyValidationError(f"{strategy['id']}: non-baseline validation must set max_variables 15 without exemption")
            _validate_weights(config.get("horizon_weights", {}), strategy["id"], registry, tolerance, max_variables)
        loaded.append({"index": entry, "config": config})
    return loaded


def _uniform_weights(variable_ids: set[str]) -> dict[str, float]:
    return {variable_id: 1.0 / len(variable_ids) for variable_id in sorted(variable_ids)}


def _current_signal(variables: dict[str, Any], variable_id: str, horizon: str) -> int:
    """Return a valid current signal; absent or malformed values are neutral."""
    variable = variables.get(variable_id)
    signal = variable.horizons[horizon].signal if variable and horizon in variable.horizons else None
    return signal if signal in {-1, 0, 1} else 0


def run_multi_strategy(
    strategies_dir: Path = DR3_STRATEGIES_DIR,
    output_path: Path = DR3_MULTI_STRATEGY_OUTPUT_PATH,
    data_dir: Path | None = None,
) -> dict[str, Any]:
    """Score every configured strategy from the current DR2 variable outputs."""
    known_ids = production_variable_ids()
    strategies = load_strategy_set(strategies_dir, known_ids)
    variables = load_variable_results(data_dir)
    output: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "current_outlook_only",
        "strategy_set_version": "1.1",
        "official_strategy": None,
        "admit_variable_count": len(known_ids),
        "strategies": {},
    }

    for loaded in strategies:
        index, config = loaded["index"], loaded["config"]
        strategy = config["strategy"]
        is_baseline = strategy["id"] == "SP-ALL"
        horizons: dict[str, Any] = {}
        for horizon in HORIZONS:
            weights = _uniform_weights(known_ids) if is_baseline else config["horizon_weights"][horizon]
            score = sum(_current_signal(variables, variable_id, horizon) * weight for variable_id, weight in weights.items())
            horizons[horizon] = {
                "score": round(score * 100, 6),
                "active_variables": "AUTO_UNIFORM_ADMIT" if is_baseline else sorted(weights),
            }
        output["strategies"][strategy["id"]] = {
            "type": strategy["type"],
            "production_eligible": bool(index.get("production_eligible", not is_baseline)),
            "horizons": horizons,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
