"""Command-line entry points for source collection and normalized caches."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import importlib
import inspect
import json
import pkgutil
from pathlib import Path
import re
from typing import Any

import yaml

from goldrush2.collectors.base import BaseCollector, CollectorError
from goldrush2.collectors.bis import BISCollector
from goldrush2.collectors.imf import IMFCollector
from goldrush2.collectors.fred import FredCollector
from goldrush2.collectors.fed import FedCollector
from goldrush2.collectors.treasury import TreasuryCollector
from goldrush2.collectors.wgc import WGCWorkbookCollector, fetch_wgc_above_ground_stocks, fetch_wgc_gold_premiums, fetch_wgc_gdt_workbook, fetch_wgc_official_changes, fetch_wgc_workbook
from goldrush2.collectors.yahoo import YahooCollector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = PROJECT_ROOT / "config" / "refresh_policies.yaml"
EXTRACTORS_PATH = PROJECT_ROOT / "src" / "goldrush2" / "extractors"


def load_policies(path: Path = POLICY_PATH) -> dict[str, dict[str, Any]]:
    """Load the checked-in variable refresh policies."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Cannot load refresh policies: {path}") from exc
    if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, dict) for key, value in payload.items()):
        raise ValueError("Refresh policies must map variable IDs to configuration objects")
    return payload


def get_all_variables(policies: dict[str, dict[str, Any]]) -> list[str]:
    """Return every variable with an implemented collection policy."""
    return sorted(policies)


def discover_extractors() -> dict[str, str]:
    """Discover extractor modules named like ``l0_001`` and map their IDs."""
    discovered: dict[str, str] = {}
    for module_info in pkgutil.iter_modules([str(EXTRACTORS_PATH)]):
        name = module_info.name
        if re.fullmatch(r"l\d_\d{3}", name):
            variable_id = name.upper().replace("_", "-")
            discovered[variable_id] = f"goldrush2.extractors.{name}"
    return dict(sorted(discovered.items()))


def _extractor_kwargs(module: Any, variable_id: str, output_path: Path) -> dict[str, Path]:
    """Build path arguments supported by an extractor's ``run`` function."""
    run = getattr(module, "run")
    parameters = inspect.signature(run).parameters
    paths: dict[str, Path] = {"output_path": output_path}
    if "cache_path" in parameters:
        if hasattr(module, "CACHE_PATH"):
            paths["cache_path"] = PROJECT_ROOT / module.CACHE_PATH
        else:
            cache_root = "imf" if variable_id == "L5-003" else "bis"
            paths["cache_path"] = PROJECT_ROOT / "data" / "cache" / cache_root / f"{variable_id}.json"
    if "raw_dir" in parameters:
        paths["raw_dir"] = PROJECT_ROOT / "data" / "raw" / "wgc"
    if "raw_path" in parameters and hasattr(module, "RAW_PATH"):
        paths["raw_path"] = Path(module.RAW_PATH)
    return {name: path for name, path in paths.items() if name in parameters}


def _print_extractor_check(extractors: dict[str, str]) -> None:
    """Print discovered extractor modules and whether they expose ``run``."""
    for variable_id, module_name in extractors.items():
        try:
            module = importlib.import_module(module_name)
            status = "OK" if callable(getattr(module, "run", None)) else "MISSING run()"
        except Exception as exc:  # pragma: no cover - defensive diagnostic output
            status = f"IMPORT ERROR: {exc}"
        print(f"{variable_id}: {module_name} [{status}]")


def _wgc_normalizer(variable_id: str):
    if variable_id == "L0-002":
        from goldrush2.extractors.l0_002 import parse_holdings_workbook

        return parse_holdings_workbook
    if variable_id == "L0-003":
        from goldrush2.extractors.l0_003 import parse_holdings_workbook

        return parse_holdings_workbook
    if variable_id == "L0-005":
        from goldrush2.extractors.l0_005 import parse_demand_workbook

        return parse_demand_workbook
    if variable_id == "L0-006":
        from goldrush2.extractors.l0_006 import parse_recycling_workbook

        return parse_recycling_workbook
    if variable_id == "L5-001":
        from goldrush2.extractors.l5_001 import parse_purchases_workbook

        return parse_purchases_workbook
    if variable_id == "L5-002":
        from goldrush2.extractors.l5_002 import parse_reserve_share_workbook

        return parse_reserve_share_workbook
    if variable_id == "L5-006":
        from goldrush2.extractors.l5_006 import parse_reductions_workbook

        return parse_reductions_workbook
    if variable_id == "L8-001":
        from goldrush2.extractors.l8_001 import parse_flows_workbook

        return parse_flows_workbook
    if variable_id == "L9-004":
        from goldrush2.extractors.l9_004 import parse_india_workbook

        return parse_india_workbook
    if variable_id == "L9-001":
        from goldrush2.extractors.l9_001 import parse_premiums_workbook

        return parse_premiums_workbook
    if variable_id == "L0-001":
        from goldrush2.extractors.l0_001 import parse_above_ground_workbook

        return parse_above_ground_workbook
    raise ValueError(f"No WGC normalizer is configured for {variable_id}")


def _wgc_fetcher(source: str):
    if source == "wgc_official_changes":
        return fetch_wgc_official_changes
    if source == "wgc_etf":
        return fetch_wgc_workbook
    if source == "wgc_gdt":
        return fetch_wgc_gdt_workbook
    if source == "wgc_premiums":
        return fetch_wgc_gold_premiums
    if source == "wgc_above_ground":
        return fetch_wgc_above_ground_stocks
    raise ValueError(f"Unsupported WGC source: {source}")


def create_collector(variable_id: str, config: dict[str, Any], *, force: bool = False) -> BaseCollector:
    """Create the policy-selected collector for one supported variable."""
    source = str(config.get("source", ""))
    cache_dir = PROJECT_ROOT / "data" / "cache" / variable_id
    raw_dir = PROJECT_ROOT / "data" / "raw"
    always_refresh = config.get("refresh_strategy") == "always_refresh"
    if source == "fred":
        series_id = str(config["series_id"])
        return FredCollector(cache_dir, series_id, raw_dir / "fred" / f"{series_id}.json", force=force, always_refresh=always_refresh)
    if source == "yahoo":
        ticker = str(config["ticker"])
        return YahooCollector(cache_dir, ticker, raw_dir / "yahoo" / f"{ticker}.json", force=force, always_refresh=always_refresh)
    if source == "bis":
        return BISCollector(PROJECT_ROOT / "data" / "cache" / "bis", raw_dir / "bis" / "Q.5A.P.A.M.USD.A.csv", force=force, always_refresh=always_refresh)
    if source == "imf_cofer":
        return IMFCollector(PROJECT_ROOT / "data" / "cache" / "imf", raw_dir / "imf" / "cofer.csv", force=force, always_refresh=always_refresh)
    if source == "fed_sep":
        return FedCollector(PROJECT_ROOT / "data" / "cache", raw_dir / "L3-005.html", force=force, always_refresh=always_refresh, snapshot_path=raw_dir / "L3-005_snapshot.html")
    if source.startswith("wgc_"):
        return WGCWorkbookCollector(cache_dir, raw_dir / "wgc", _wgc_fetcher(source), _wgc_normalizer(variable_id), force=force, always_refresh=always_refresh)
    if source == "treasury":
        if config.get("endpoint") == "mts_table_3":
            from goldrush2.extractors import l4_008

            return TreasuryCollector(cache_dir, l4_008.SOURCE_URL, {"filter": "line_code_nbr:in:(130,360)", "sort": "record_date"}, l4_008.RAW_PATH, l4_008.parse_observations, force=force, always_refresh=always_refresh)
        if config.get("endpoint") == "mspd_table_3":
            from goldrush2.extractors import l4_009

            start = (date.today() - timedelta(days=365 * 2)).isoformat()
            filters = {"filter": f"record_date:gte:{start}", "sort": "record_date,src_line_nbr", "fields": "record_date,security_type_desc,security_class1_desc,security_class2_desc,maturity_date,outstanding_amt,src_line_nbr"}
            return TreasuryCollector(cache_dir, l4_009.SOURCE_URL, filters, l4_009.RAW_PATH, l4_009.parse_observations, force=force, always_refresh=always_refresh)
    raise ValueError(f"No BaseCollector adapter is available for {variable_id} ({source})")


def _print_summary(variable_id: str, collector: BaseCollector, rows: list[dict[str, Any]]) -> None:
    latest = max((str(row["date"]) for row in rows), default="none")
    warning = f" warning={collector.warning}" if collector.warning else ""
    print(f"{variable_id}: action={collector.action} count={len(rows)} latest={latest}{warning}")


def cmd_collect(args: argparse.Namespace) -> int:
    policies = load_policies()
    variables = get_all_variables(policies) if args.all else [args.variable]
    failures = 0
    for variable_id in variables:
        config = policies.get(variable_id)
        if config is None:
            print(f"{variable_id}: unknown variable policy")
            failures += 1
            continue
        if config.get("source") == "cme_futures":
            print(f"{variable_id}: action=delegated detail=collector remains internal to the mixed CME/FRED extractor")
            continue
        try:
            collector = create_collector(variable_id, config, force=args.force)
            collector.verbose = getattr(args, "verbose", 0)
            if args.dry_run:
                print(f"{variable_id}: action=planned strategy={config.get('refresh_strategy')} source={config.get('source')}")
                continue
            _print_summary(variable_id, collector, collector.run())
        except (CollectorError, KeyError, ValueError) as exc:
            print(f"{variable_id}: action=failed detail={exc}")
            failures += 1
    return 1 if failures else 0


def cmd_extract(args: argparse.Namespace) -> int:
    extractors = discover_extractors()
    if getattr(args, "check", False):
        _print_extractor_check(extractors)
        return 0
    variable_id = args.variable.upper()
    module_name = extractors.get(variable_id)
    if module_name is None:
        print(f"{variable_id}: no extractor command is configured")
        return 1

    try:
        module = importlib.import_module(module_name)
        run = getattr(module, "run")
        output_path = PROJECT_ROOT / "data" / "current" / f"{variable_id}.json"
        output = run(**_extractor_kwargs(module, variable_id, output_path))
    except (OSError, ValueError, KeyError, AttributeError, TypeError, ImportError, RuntimeError) as exc:
        print(f"{variable_id}: action=failed detail={exc}")
        return 1
    if getattr(args, "pretty", False):
        print(json.dumps(output, indent=2, default=str))
    elif getattr(args, "print_json", False):
        print(json.dumps(output, default=str))
    else:
        observation_date = output.get("observation_date") if isinstance(output, dict) else None
        print(f"{variable_id}: action=extract observation_date={observation_date}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gr2")
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect", help="refresh normalized source caches")
    collect.add_argument("variable", nargs="?", help="variable ID to refresh")
    collect.add_argument("--all", action="store_true", help="refresh every configured variable")
    collect.add_argument("--force", action="store_true", help="ignore source-date checks and request full refreshes")
    collect.add_argument("--dry-run", action="store_true", help="show collection plans without source requests")
    collect.add_argument("-v", "--verbose", action="count", default=0, help="show execution details; repeat for more detail")
    collect.set_defaults(handler=cmd_collect)
    extract = commands.add_parser("extract", help="build current variable output from normalized cache")
    extract.add_argument("variable", nargs="?", help="variable ID")
    output_group = extract.add_mutually_exclusive_group()
    output_group.add_argument("--print", dest="print_json", action="store_true", help="print compact JSON after extraction")
    output_group.add_argument("--pretty", action="store_true", help="print indented JSON after extraction")
    extract.add_argument("--check", action="store_true", help="list discovered extractors and mapping status")
    extract.set_defaults(handler=cmd_extract)
    args = parser.parse_args(argv)
    if args.command == "collect" and bool(args.variable) == bool(args.all):
        parser.error("collect requires either a variable ID or --all")
    if args.command == "extract" and not args.check and not args.variable:
        parser.error("extract requires a variable ID or --check")
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
