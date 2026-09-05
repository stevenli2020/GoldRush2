"""Optional Gemini-assisted scoring for L3-006.

The collector and extractor remain usable without this module or an API key.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from google import genai
except ImportError:  # pragma: no cover - environment dependent
    genai = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - environment dependent
    load_dotenv = None

from goldrush2.paths import DR2_ROOT as ROOT
CACHE_PATH = ROOT / "data/cache/L3-006.json"
SCORES_PATH = ROOT / "data/ai_scores/L3-006_scores.json"
RAW_DIR = ROOT / "data/ai_scores/raw"
OUTPUT_PATH = ROOT / "data/current/L3-006.json"
MIN_SCORE_CHANGE = 1.0

PROMPT_PHASE1 = """Assess this FOMC statement against the prior statement. Return JSON only with baseline_score (0-100), coverage (0-1), quality_status (PASS, FLAG, or BLOCKED), and explanation. 0 is strongly dovish and 100 strongly hawkish. Use only supplied text.\nCURRENT:\n{current}\nPRIOR:\n{prior}"""
PROMPT_PHASE2 = """You are a {role}. Assess the hawkishness of the current FOMC statement compared with the prior statement. Return JSON only: {{\"hawkish_score\": 0-100, \"explanation\": \"brief\"}}.\nCURRENT:\n{current}\nPRIOR:\n{prior}"""
ROLES = ("CENTRAL_BANK_POLICY_ECONOMIST", "GOLD_CROSS_ASSET_STRATEGIST", "FINANCIAL_COMMUNICATIONS_ANALYST")


def _load_project_env() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env", override=False)


def _load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise ValueError(f"Corrupt JSON cache: {path}") from exc


def _call_gemini(prompt: str, model: str) -> dict[str, Any]:
    if genai is None:
        raise RuntimeError("Install google-genai, python-dotenv, beautifulsoup4, and pandas to enable Gemini scoring")
    _load_project_env()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    client = genai.Client(api_key=key)
    response = client.models.generate_content(model=model, contents=prompt, config={"response_mime_type": "application/json", "temperature": 0})
    text = getattr(response, "text", "") or ""
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini response must be a JSON object")
    return parsed


def _confidence(status: str) -> float:
    return {"PASS": 1.0, "FLAG": 0.5, "BLOCKED": 0.0}.get(status, 0.0)


def score_l3_006(force: bool = False, call: Callable[[str, str], dict[str, Any]] | None = None, cache_path: Path | None = None, output_path: Path | None = None, verbose: int = 0) -> dict[str, Any]:
    _load_project_env()
    cache_path = Path(cache_path or CACHE_PATH)
    output_path = Path(output_path or OUTPUT_PATH)
    statements = sorted(_load(cache_path, []), key=lambda row: str(row.get("date", "")))
    if not statements:
        raise ValueError("L3-006 cache contains no statements")
    current = statements[-1]
    prior = statements[-2] if len(statements) > 1 else None
    scores = _load(SCORES_PATH, {})
    if not force and current["date"] in scores:
        if verbose >= 1:
            print(f"[ai] using cached L3-006 score for {current['date']}")
        return _write_output(current, statements, scores[current["date"]], output_path)
    invoke = call or _call_gemini
    prior_text = prior.get("text", "") if prior else "(none available)"
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    try:
        if verbose >= 1:
            print(f"[ai] running Gemini baseline and {len(ROLES)} jury assessments with model={model}")
        baseline = invoke(PROMPT_PHASE1.format(current=current.get("text", ""), prior=prior_text), model)
        baseline_score = float(baseline["baseline_score"])
        coverage = float(baseline.get("coverage", 1.0))
        quality = str(baseline.get("quality_status", "FLAG")).upper()
        if not 0 <= baseline_score <= 100 or not 0 <= coverage <= 1 or quality not in {"PASS", "FLAG", "BLOCKED"}:
            raise ValueError("Invalid baseline score response")
        jury = []
        raw_jury: dict[str, Any] = {}
        for role in ROLES:
            result = invoke(PROMPT_PHASE2.format(role=role, current=current.get("text", ""), prior=prior_text), model)
            score = float(result["hawkish_score"])
            if not 0 <= score <= 100:
                raise ValueError("Invalid jury score response")
            jury.append(score); raw_jury[role] = result
        jury_avg = round(sum(jury) / len(jury), 1)
        entry = {"baseline": round(baseline_score, 1), "jury_avg": jury_avg, "blended": round((baseline_score + jury_avg) / 2, 1), "coverage": coverage, "quality_status": quality, "model": model, "temperature": 0.0, "run_at": datetime.now(timezone.utc).isoformat(), "raw_phase1": baseline, "raw_jury": raw_jury}
        if prior and prior["date"] in scores:
            change = baseline_score - float(scores[prior["date"]]["baseline"])
            entry["change"] = change
            entry["signal"] = 1 if change <= -MIN_SCORE_CHANGE else -1 if change >= MIN_SCORE_CHANGE else 0
            entry["signal_reason"] = "change below threshold" if entry["signal"] == 0 else "baseline score change"
        else:
            entry["change"], entry["signal"], entry["signal_reason"] = None, 0, "no scored prior statement"
        scores[current["date"]] = entry
        SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCORES_PATH.write_text(json.dumps(scores, indent=2) + "\n", encoding="utf-8")
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"{current['date']}_phase1.json").write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        (RAW_DIR / f"{current['date']}_jury.json").write_text(json.dumps(raw_jury, indent=2) + "\n", encoding="utf-8")
        return _write_output(current, statements, entry, output_path)
    except Exception as exc:
        if verbose >= 1:
            print(f"[ai] scoring failed: {exc}")
        from goldrush2.dr2.extractors.l3_006 import build_output
        base = build_output(statements)
        base["ai_status"] = "error"
        base["ai"] = {"error": str(exc)}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return base


def _write_output(current: dict[str, Any], statements: list[dict[str, Any]], entry: dict[str, Any], output_path: Path | None = None) -> dict[str, Any]:
    output_path = Path(output_path or OUTPUT_PATH)
    from goldrush2.dr2.extractors.l3_006 import build_output
    output = build_output(statements)
    output["ai_status"] = "success"
    output["ai"] = entry
    confidence = _confidence(entry.get("quality_status", "BLOCKED"))
    signal = entry.get("signal", 0)
    for horizon in ("1-5d", "1-3m"):
        output["horizons"][horizon] = {"signal": signal, "confidence": confidence, "evidence": {"baseline": entry.get("baseline"), "blended": entry.get("blended"), "change": entry.get("change")}}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output
