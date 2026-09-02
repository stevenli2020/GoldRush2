"""Tests for extractor discovery and CLI output modes."""

import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from goldrush2 import cli


def test_discover_extractors_finds_all_current_modules():
    discovered = cli.discover_extractors()

    assert len(discovered) == 35
    assert discovered["L0-006"] == "goldrush2.extractors.l0_006"
    assert discovered["L7-003"] == "goldrush2.extractors.l7_003"


def test_extract_check_lists_discovered_mapping(monkeypatch, capsys):
    monkeypatch.setattr(cli, "discover_extractors", lambda: {"L0-006": "goldrush2.extractors.l0_006"})

    assert cli.main(["extract", "--check"]) == 0

    output = capsys.readouterr().out
    assert "L0-006: goldrush2.extractors.l0_006 [OK]" in output


def test_extract_runs_discovered_module_and_prints_summary(monkeypatch, tmp_path, capsys):
    def run(*, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("{}", encoding="utf-8")
        return {"observation_date": "2026-09-02"}

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli, "discover_extractors", lambda: {"L0-006": "fake.extractor"})
    monkeypatch.setattr(cli.importlib, "import_module", lambda name: SimpleNamespace(run=run))

    assert cli.main(["extract", "L0-006"]) == 0

    assert "L0-006: action=extract observation_date=2026-09-02" in capsys.readouterr().out


def test_extract_print_emits_compact_json(monkeypatch, tmp_path, capsys):
    result = {"variable_id": "L7-003", "horizons": {"1-3y": {"signal": 1}}}

    def run(*, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli, "discover_extractors", lambda: {"L7-003": "fake.extractor"})
    monkeypatch.setattr(cli.importlib, "import_module", lambda name: SimpleNamespace(run=run))

    assert cli.main(["extract", "L7-003", "--print"]) == 0

    captured = capsys.readouterr().out
    assert json.loads(captured) == result
    assert "\n  \"variable_id\"" not in captured


def test_extract_pretty_emits_indented_json(monkeypatch, tmp_path, capsys):
    result = {"variable_id": "L7-003", "value": 1}

    def run(*, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result), encoding="utf-8")
        return result

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cli, "discover_extractors", lambda: {"L7-003": "fake.extractor"})
    monkeypatch.setattr(cli.importlib, "import_module", lambda name: SimpleNamespace(run=run))

    assert cli.main(["extract", "L7-003", "--pretty"]) == 0

    captured = capsys.readouterr().out
    assert json.loads(captured) == result
    assert '\n  "variable_id"' in captured


def test_extract_unknown_variable_returns_error(monkeypatch, capsys):
    monkeypatch.setattr(cli, "discover_extractors", lambda: {})

    assert cli.main(["extract", "L9-999"]) == 1
    assert "L9-999: no extractor command is configured" in capsys.readouterr().out
