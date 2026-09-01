import json
from io import BytesIO
from urllib.error import URLError

import pytest

from goldrush2.collectors import fred


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return BytesIO(json.dumps(self.payload).encode("utf-8"))

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_fetch_series_returns_valid_values_ignores_missing_and_writes_raw(monkeypatch, tmp_path):
    payload = {
        "observations": [
            {"date": "2026-08-25", "value": "2.32"},
            {"date": "2026-08-26", "value": "."},
            {"date": "2026-08-27", "value": "2.34"},
        ]
    }
    monkeypatch.setattr(fred, "urlopen", lambda url, timeout: FakeResponse(payload))
    raw_path = tmp_path / "DFII10.json"

    observations = fred.fetch_series("DFII10", api_key="test-key", raw_path=raw_path)

    assert observations == [
        {"date": "2026-08-25", "value": 2.32},
        {"date": "2026-08-27", "value": 2.34},
    ]
    assert json.loads(raw_path.read_text(encoding="utf-8")) == payload


def test_fetch_series_requires_api_key(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    with pytest.raises(fred.FredCredentialError, match="FRED_API_KEY is not set"):
        fred.fetch_series("DFII10")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"observations": "not-a-list"},
        {"observations": ["not-an-object"]},
        {"observations": [{"date": "not-a-date", "value": "2.0"}]},
        {"observations": [{"date": "2026-08-27", "value": "bad"}]},
        {"observations": [{"date": "2026-08-27", "value": "NaN"}]},
    ],
)
def test_parse_observations_rejects_malformed_data(payload):
    with pytest.raises(fred.FredDataError):
        fred.parse_observations(payload)


def test_failed_request_does_not_overwrite_raw_cache(monkeypatch, tmp_path):
    raw_path = tmp_path / "DFII10.json"
    raw_path.write_text('{"preserved": true}\n', encoding="utf-8")
    monkeypatch.setattr(fred, "urlopen", lambda url, timeout: (_ for _ in ()).throw(URLError("offline")))

    with pytest.raises(fred.FredNetworkError, match="offline"):
        fred.fetch_series("DFII10", api_key="test-key", raw_path=raw_path)

    assert raw_path.read_text(encoding="utf-8") == '{"preserved": true}\n'
