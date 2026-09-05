import json
import os
import time

import pytest

from goldrush2.dr2.collectors import treasury


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_fetch_handles_pagination_and_preserves_pages(monkeypatch, tmp_path):
    payloads = [
        {"data": [{"id": 1}], "meta": {"pagination": {"pages": 2}}},
        {"data": [{"id": 2}], "meta": {"pagination": {"pages": 2}}},
    ]
    monkeypatch.setattr(treasury, "urlopen", lambda url, timeout: Response(payloads.pop(0)))
    cache = tmp_path / "table.json"
    result = treasury.fetch_treasury_table("https://example.test/table", {"filter": "x:eq:y"}, cache)
    assert treasury.flatten_data(result) == [{"id": 1}, {"id": 2}]
    assert result["source_status"] == "LIVE"
    assert len(json.loads(cache.read_text())["pages"]) == 2


def test_fresh_cache_fallback(monkeypatch, tmp_path):
    cache = tmp_path / "table.json"
    cache.write_text(json.dumps({"pages": [{"data": [{"id": 1}]}]}))
    monkeypatch.setattr(treasury, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(treasury.TreasuryError("offline")))
    result = treasury.fetch_treasury_table("https://example.test/table", {}, cache)
    assert result["source_status"] == "CACHED"
    assert "fallback_note" in result


def test_stale_cache_raises(monkeypatch, tmp_path):
    cache = tmp_path / "table.json"
    cache.write_text(json.dumps({"pages": [{"data": []}]}))
    old = time.time() - 8 * 86400
    os.utime(cache, (old, old))
    monkeypatch.setattr(treasury, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(treasury.TreasuryError("offline")))
    with pytest.raises(treasury.TreasuryError, match="STALE DATA"):
        treasury.fetch_treasury_table("https://example.test/table", {}, cache)


def test_flatten_ignores_non_object_rows():
    assert treasury.flatten_data({"pages": [{"data": [{"x": 1}, "bad"]}]}) == [{"x": 1}]
