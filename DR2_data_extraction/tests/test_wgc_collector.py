"""Tests for the shared WGC workbook collector."""

import io
import os
import time
import zipfile

from openpyxl import Workbook

from goldrush2.dr2.collectors import wgc


def xlsx_bytes() -> bytes:
    workbook = Workbook()
    workbook.active["A1"] = "test"
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def test_download_and_validate_xlsx(monkeypatch, tmp_path):
    page = b'<a href="/download/file/ETF_Flows_2026-09-01_1200.xlsx">download</a>'
    monkeypatch.setattr(wgc, "_request", lambda url, **kwargs: page if url == wgc.WGC_PAGE_URL else xlsx_bytes())
    path = wgc.fetch_wgc_workbook(tmp_path)
    assert path is not None and path.name == "ETF_Flows_2026-09-01_1200.xlsx"
    assert path.read_bytes().startswith(b"PK\x03\x04")


def test_fresh_cache_is_reused_without_download(monkeypatch, tmp_path):
    path = tmp_path / "ETF_Flows_cached.xlsx"
    path.write_bytes(xlsx_bytes())
    monkeypatch.setattr(wgc, "_request", lambda *args, **kwargs: (_ for _ in ()).throw(wgc.WGCError("offline")))
    assert wgc.fetch_wgc_workbook(tmp_path) == path
    assert not wgc.LAST_FETCH_USED_CACHE


def test_stale_cache_returns_none(monkeypatch, tmp_path):
    path = tmp_path / "ETF_Flows_cached.xlsx"
    path.write_bytes(xlsx_bytes())
    old = time.time() - 8 * 86400
    os.utime(path, (old, old))
    monkeypatch.setattr(wgc, "_request", lambda *args, **kwargs: (_ for _ in ()).throw(wgc.WGCError("offline")))
    assert wgc.fetch_wgc_workbook(tmp_path) is None
    assert wgc.LAST_FETCH_STALE


def test_invalid_xlsx_is_not_cached(monkeypatch, tmp_path):
    page = b'<a href="/download/file/ETF_Flows_2026-09-01_1200.xlsx">download</a>'
    monkeypatch.setattr(wgc, "_request", lambda url, **kwargs: page if url == wgc.WGC_PAGE_URL else b"not excel")
    assert wgc.fetch_wgc_workbook(tmp_path) is None
    assert list(tmp_path.glob("*.xlsx")) == []


def test_missing_workbook_link_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(wgc, "_request", lambda *args, **kwargs: b"<html>login</html>")
    assert wgc.fetch_wgc_workbook(tmp_path) is None


def test_cookie_header_from_json(monkeypatch, tmp_path):
    cookie_path = tmp_path / "cookies.json"
    cookie_path.write_text('[{"name":"session","value":"abc"}]', encoding="utf-8")
    monkeypatch.setenv("WGC_COOKIES_PATH", str(cookie_path))
    assert wgc._cookie_header() == "session=abc"


def test_official_changes_target(monkeypatch, tmp_path):
    page = b'<a href="/download/file/7741/Changes_latest_as_of_Aug2026_IFS.xlsx">download</a>'
    monkeypatch.setattr(wgc, "_request", lambda url, **kwargs: page if url == wgc.WGC_OFFICIAL_CHANGES_PAGE_URL else xlsx_bytes())
    path = wgc.fetch_wgc_official_changes(tmp_path)
    assert path is not None
    assert path.name == "Changes_latest_as_of_Aug2026_IFS.xlsx"


def test_official_holdings_target(monkeypatch, tmp_path):
    page = b'<a href="/download/file/7739/World_official_gold_holdings_as_of_Aug2026_IFS.xlsx ">download</a>'
    monkeypatch.setattr(wgc, "_request", lambda url, **kwargs: page if url == wgc.WGC_OFFICIAL_HOLDINGS_PAGE_URL else xlsx_bytes())
    path = wgc.fetch_wgc_official_holdings(tmp_path)
    assert path is not None
    assert path.name == "World_official_gold_holdings_as_of_Aug2026_IFS.xlsx"


def test_gdt_target(monkeypatch, tmp_path):
    page = b'<a href="/download/file/GDT_Tables_Q2\'26_EN.xlsx">download</a>'
    monkeypatch.setattr(wgc, "_request", lambda url, **kwargs: page if url == wgc.WGC_GDT_PAGE_URL else xlsx_bytes())
    path = wgc.fetch_wgc_gdt_workbook(tmp_path)
    assert path is not None
    assert path.name == "GDT_Tables_Q2'26_EN.xlsx"
