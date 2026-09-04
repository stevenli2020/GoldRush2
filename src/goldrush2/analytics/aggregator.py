"""DR3 Aggregation Engine for GoldRush2."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

from goldrush2.analytics.models import AggregatedResult, HorizonScore, VariableResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WEIGHTS_FILE = PROJECT_ROOT / "config" / "weights_v1.yaml"
SCORES_OUTPUT_FILE = PROJECT_ROOT / "data" / "current" / "current_scores.json"
HORIZONS = ["1-5d", "1-3m", "1-3y", "3-10y"]

def load_weights(weights_path: Optional[Path] = None) -> dict:
    path = weights_path or WEIGHTS_FILE
    if not path.exists(): raise FileNotFoundError(f"Weight configuration not found: {path}")
    with open(path, "r", encoding="utf-8") as f: config = yaml.safe_load(f)
    return config

def load_variable_results(data_dir: Optional[Path] = None) -> dict[str, VariableResult]:
    directory = data_dir or PROJECT_ROOT / "data" / "current"
    results = {}
    if not directory.exists(): return results
    for json_file in sorted(directory.glob("L*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f: data = json.load(f)
            results[data.get("variable_id", json_file.stem)] = VariableResult.from_dict(data)
        except Exception as e: print(f"WARNING: Failed to parse {json_file.name}: {e}", file=sys.stderr)
    return results

def aggregate_horizon(horizon: str, raw_weights: dict[str, float], variables: dict[str, VariableResult]) -> tuple[HorizonScore, list[str]]:
    warnings = []
    
    # Exclude only explicitly inapplicable outputs. Missing variables remain
    # configured so their weight reduces data availability.
    applicable_raw_weights = {}
    for var_id, weight in raw_weights.items():
        if weight <= 0: continue
        hs = variables[var_id].horizons.get(horizon) if var_id in variables else None
        if hs is not None and hs.evidence.data.applicable is False:
            continue
        applicable_raw_weights[var_id] = weight

    # Rank before checking missing data so missing core variables are visible.
    total_applicable = sum(applicable_raw_weights.values())
    normalized_applicable = {k: v / total_applicable for k, v in applicable_raw_weights.items()} if total_applicable > 0 else {}
    
    if normalized_applicable:
        top_5_vars = sorted(normalized_applicable.keys(), key=lambda k: normalized_applicable[k], reverse=True)[:5]
        for var_id in top_5_vars:
            if var_id not in variables or variables[var_id].horizons.get(horizon) is None or variables[var_id].horizons[horizon].confidence <= 0.0:
                warnings.append(f"🔴 HIGH_WEIGHT_MISSING: {var_id} (top-5 core variable missing or degraded)")

    # 3. Compute score
    valid_sum = 0.0 # Score denominator: sum of W * C
    weighted_signal_sum = 0.0
    weighted_conf_sum = 0.0
    contributions = []
    low_conf_contributors = []
    contributing_count = 0
    
    available_weight = 0.0
    for var_id, norm_weight in normalized_applicable.items():
        variable = variables.get(var_id)
        if variable is None or horizon not in variable.horizons:
            continue
        hs = variable.horizons[horizon]
        if hs.evidence.data.applicable is False:
            continue
        if hs.confidence <= 0.0: continue
        
        valid_sum += norm_weight * hs.confidence
        available_weight += norm_weight
        weighted_signal_sum += hs.signal * norm_weight * hs.confidence
        weighted_conf_sum += norm_weight * hs.confidence
        contributing_count += 1
        contributions.append((var_id, hs.signal * norm_weight * hs.confidence))
        
        if 0 < hs.confidence < 0.5:
            low_conf_contributors.append({"variable_id": var_id, "confidence": hs.confidence})

    configured_ids = set(raw_weights.keys())
    for var_id in sorted(set(variables.keys()) - configured_ids):
        warnings.append(f"UNMAPPED: {var_id} found in data but not in weight config; ignoring")

    if valid_sum <= 0:
        return HorizonScore(horizon=horizon, score=0, raw_score=0.0, confidence=0.0, data_availability=0.0, status="DEGRADED", contributing_variables=0, total_configured_variables=len(raw_weights), top_bullish=[], top_bearish=[], low_confidence_contributors=[]), warnings

    raw_score = max(-1.0, min(1.0, weighted_signal_sum / valid_sum))
    data_availability = available_weight
    status = "NORMAL" if data_availability >= 0.6 else "DEGRADED"
    final_score = int(round(raw_score * 100))
    overall_confidence = weighted_conf_sum / available_weight

    contributions.sort(key=lambda x: x[1], reverse=True)
    top_bullish = [vid for vid, val in contributions[:5] if val > 0]
    top_bearish = [vid for vid, val in contributions[-5:] if val < 0]
    top_bearish.reverse()

    return HorizonScore(horizon=horizon, score=final_score, raw_score=raw_score, confidence=overall_confidence, data_availability=data_availability, status=status, contributing_variables=contributing_count, total_configured_variables=len(raw_weights), top_bullish=top_bullish, top_bearish=top_bearish, low_confidence_contributors=low_conf_contributors), warnings

def run_analytics(weights_path: Optional[Path] = None, data_dir: Optional[Path] = None, output_path: Optional[Path] = None) -> AggregatedResult:
    weight_config = load_weights(weights_path)
    variables = load_variable_results(data_dir)
    all_warnings = []
    horizon_scores = {}

    for horizon in HORIZONS:
        raw_weights = weight_config["horizons"].get(horizon, {})
        if not raw_weights:
            all_warnings.append(f"HORIZON EMPTY: No weights configured for '{horizon}'")
            horizon_scores[horizon] = HorizonScore(horizon=horizon, score=0, raw_score=0.0, confidence=0.0, data_availability=0.0, status="DEGRADED", contributing_variables=0, total_configured_variables=0, top_bullish=[], top_bearish=[], low_confidence_contributors=[])
            continue
        score, warnings = aggregate_horizon(horizon, raw_weights, variables)
        horizon_scores[horizon] = score
        all_warnings.extend(warnings)

    result = AggregatedResult(generated_at=datetime.now(timezone.utc).isoformat(), weight_schema_version=weight_config.get("version", "unknown"), horizons=horizon_scores, warnings=all_warnings)
    out_path = output_path or SCORES_OUTPUT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f: json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
    return result
