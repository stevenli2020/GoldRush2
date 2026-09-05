"""Tests for policy-independent normalized cache orchestration."""

import os

import pytest

from goldrush2.dr2.collectors.base import BaseCollector, SourceUnavailableError


class FakeCollector(BaseCollector):
    def __init__(self, cache_dir, *, latest="2024-01-02", full=None, incremental=None, force=False, always_refresh=False, verbose=0, latest_error=None, incremental_error=None):
        super().__init__(cache_dir, force=force, always_refresh=always_refresh, verbose=verbose)
        self.latest = latest
        self.full = full if full is not None else [{"date": "2024-01-01", "value": 1.0}]
        self.incremental = incremental if incremental is not None else [{"date": "2024-01-02", "value": 2.0}]
        self.latest_error = latest_error
        self.incremental_error = incremental_error
        self.full_calls = 0
        self.incremental_calls = 0

    def fetch_latest_observation_date(self):
        if self.latest_error:
            raise self.latest_error
        return self.latest

    def download_full(self):
        self.full_calls += 1
        return self.full

    def download_incremental(self, since_date):
        self.incremental_calls += 1
        if self.incremental_error:
            raise self.incremental_error
        return self.incremental


def test_missing_cache_downloads_full(tmp_path):
    collector = FakeCollector(tmp_path)
    assert collector.run() == [{"date": "2024-01-01", "value": 1.0}]
    assert collector.action == "full"
    assert collector.load_meta()["last_observation_date"] == "2024-01-01"


def test_unchanged_source_skips_download(tmp_path):
    FakeCollector(tmp_path).run()
    collector = FakeCollector(tmp_path, latest="2024-01-01")
    assert collector.run()[0]["value"] == 1.0
    assert collector.action == "skip"
    assert collector.full_calls == collector.incremental_calls == 0


def test_newer_source_merges_incremental_rows(tmp_path):
    FakeCollector(tmp_path).run()
    collector = FakeCollector(tmp_path)
    assert collector.run() == [{"date": "2024-01-01", "value": 1.0}, {"date": "2024-01-02", "value": 2.0}]
    assert collector.action == "incremental"
    assert collector.incremental_calls == 1


def test_incremental_failure_falls_back_to_full_download(tmp_path):
    FakeCollector(tmp_path).run()
    full = [{"date": "2024-01-01", "value": 10.0}, {"date": "2024-01-02", "value": 20.0}]
    collector = FakeCollector(tmp_path, full=full, incremental_error=SourceUnavailableError("incremental unavailable"))
    assert collector.run() == full
    assert collector.action == "full"
    assert collector.full_calls == collector.incremental_calls == 1


def test_source_unavailable_uses_existing_cache_with_warning(tmp_path):
    FakeCollector(tmp_path).run()
    collector = FakeCollector(tmp_path, latest_error=SourceUnavailableError("offline"))
    assert collector.run() == [{"date": "2024-01-01", "value": 1.0}]
    assert collector.action == "cache"
    assert "SOURCE UNAVAILABLE" in collector.warning


def test_force_full_download_records_timestamp(tmp_path):
    FakeCollector(tmp_path).run()
    collector = FakeCollector(tmp_path, full=[{"date": "2024-01-03", "value": 3.0}], force=True)
    assert collector.run() == [{"date": "2024-01-03", "value": 3.0}]
    assert collector.action == "full"
    assert collector.load_meta()["force_refreshed_at"].endswith("Z")


def test_atomic_write_replaces_without_leaving_temporary_file(tmp_path, monkeypatch):
    collector = FakeCollector(tmp_path)
    calls = []
    replace = os.replace
    monkeypatch.setattr("goldrush2.dr2.collectors.base.os.replace", lambda source, target: (calls.append((source, target)), replace(source, target))[1])
    collector.run()
    assert calls
    assert collector.cache_path.exists()
    assert not collector.cache_path.with_suffix(".json.tmp").exists()


def test_deduplicate_keeps_latest_record_for_each_date(tmp_path):
    collector = FakeCollector(tmp_path)
    rows = collector._deduplicate([{"date": "2024-01-02", "value": 1.0}, {"date": "2024-01-01", "value": 1.0}, {"date": "2024-01-02", "value": 2.0}])
    assert rows == [{"date": "2024-01-01", "value": 1.0}, {"date": "2024-01-02", "value": 2.0}]


def test_verbose_output_increases_execution_detail(tmp_path, capsys):
    collector = FakeCollector(tmp_path, verbose=3)
    collector.run()
    output = capsys.readouterr().out
    assert "normalized cache missing" in output
    assert "normalized cache=" in output
    assert "metadata=" in output


def test_always_refresh_uses_incremental_without_setting_manual_force_timestamp(tmp_path):
    FakeCollector(tmp_path).run()
    collector = FakeCollector(tmp_path, full=[{"date": "2024-01-02", "value": 2.0}], always_refresh=True)
    collector.run()
    assert collector.action == "incremental"
    assert collector.load_meta()["force_refreshed_at"] is None
