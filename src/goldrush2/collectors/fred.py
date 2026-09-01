"""Series-agnostic collection from the FRED observations API."""

from __future__ import annotations

import json
import math
import os
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredError(RuntimeError):
    """Base error for FRED collection failures."""


class FredCredentialError(FredError):
    """Raised when the FRED API credential is missing or rejected."""


class FredNetworkError(FredError):
    """Raised when FRED cannot be reached or returns an HTTP failure."""


class FredDataError(FredError):
    """Raised when FRED returns malformed observation data."""


def parse_observations(payload: Any) -> list[dict[str, str | float]]:
    """Parse valid dated numeric observations from a FRED API payload."""
    if not isinstance(payload, dict) or not isinstance(payload.get("observations"), list):
        raise FredDataError("FRED response does not contain an observations list")

    parsed: list[dict[str, str | float]] = []
    for position, observation in enumerate(payload["observations"]):
        if not isinstance(observation, dict):
            raise FredDataError(f"FRED observation {position} is not an object")

        observation_date = observation.get("date")
        raw_value = observation.get("value")
        if raw_value == ".":
            continue
        if not isinstance(observation_date, str):
            raise FredDataError(f"FRED observation {position} has no valid date")

        try:
            date.fromisoformat(observation_date)
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise FredDataError(f"FRED observation {position} is malformed") from exc
        if not math.isfinite(value):
            raise FredDataError(f"FRED observation {position} is not finite")

        parsed.append({"date": observation_date, "value": value})

    return parsed


def _write_raw_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(path)


def fetch_series(
    series_id: str,
    *,
    api_key: str | None = None,
    raw_path: Path | None = None,
    timeout: float = 30,
) -> list[dict[str, str | float]]:
    """Fetch a complete FRED series and optionally save its raw JSON payload."""
    resolved_api_key = api_key or os.getenv("FRED_API_KEY")
    if not resolved_api_key:
        raise FredCredentialError("FRED_API_KEY is not set")

    query = urlencode(
        {
            "series_id": series_id,
            "api_key": resolved_api_key,
            "file_type": "json",
            "limit": 100000,
        }
    )
    try:
        with urlopen(f"{FRED_OBSERVATIONS_URL}?{query}", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code in {400, 401, 403}:
            raise FredCredentialError(f"FRED rejected the request (HTTP {exc.code})") from exc
        raise FredNetworkError(f"FRED request failed (HTTP {exc.code})") from exc
    except URLError as exc:
        raise FredNetworkError(f"FRED is unavailable: {exc.reason}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FredDataError("FRED returned invalid JSON") from exc

    observations = parse_observations(payload)
    if raw_path is not None:
        _write_raw_payload(raw_path, payload)
    return observations


def load_cached_series(path: Path) -> list[dict[str, str | float]]:
    """Load and parse a previously saved raw FRED payload."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FredDataError(f"Cannot read cached FRED response: {path}") from exc
    return parse_observations(payload)
