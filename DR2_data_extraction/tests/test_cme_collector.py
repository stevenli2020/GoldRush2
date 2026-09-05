from datetime import date
import json

import pytest

from goldrush2.dr2.collectors import cme


def test_parse_fed_futures_text_extracts_contracts_and_rates():
    text = "30D FED FD FUT\nAUG26 96.3675 (\nSEP26 96.3050 (\nTOTAL"
    rows = cme.parse_fed_futures_text(text)
    assert rows[0]["contract"] == "ZQQ26"
    assert rows[0]["expiry_date"] == "2026-08-31"
    assert rows[0]["settlement_price"] == pytest.approx(96.3675)
    assert rows[0]["implied_rate"] == pytest.approx(3.6325)


def test_parse_rejects_missing_table():
    with pytest.raises(cme.CmeDataError, match="section not found"):
        cme.parse_fed_futures_text("other table")


def test_fetch_preserves_cache_when_downloaded_pdf_is_malformed(monkeypatch, tmp_path):
    raw = tmp_path / "bulletin.pdf"
    manifest = tmp_path / "manifest.json"
    raw.write_bytes(b"%PDF-old")

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"not a pdf"

    monkeypatch.setattr(cme, "urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(cme.CmeDataError):
        cme.fetch_cme_bulletin(raw_path=raw, manifest_path=manifest)
    assert raw.read_bytes() == b"%PDF-old"


def test_fetch_writes_manifest_after_valid_parse(monkeypatch, tmp_path):
    raw = tmp_path / "bulletin.pdf"
    manifest = tmp_path / "manifest.json"

    monkeypatch.setattr(cme, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(cme.CmeNetworkError("offline")))
    with pytest.raises(cme.CmeNetworkError):
        cme.fetch_cme_bulletin(raw_path=raw, manifest_path=manifest)
    assert not manifest.exists()

