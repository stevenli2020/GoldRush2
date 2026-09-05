"""Authoritative project locations for the stage-based GR2 layout."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DR1_ROOT = PROJECT_ROOT / "DR1_definition"
DR2_ROOT = PROJECT_ROOT / "DR2_data_extraction"
DR3_ROOT = PROJECT_ROOT / "DR3_data_analytics"
DR4_ROOT = PROJECT_ROOT / "DR4_data_presentation"
DR5_ROOT = PROJECT_ROOT / "DR5_operations"

DR2_CONFIG_DIR = DR2_ROOT / "config"
DR2_DATA_DIR = DR2_ROOT / "data"
DR2_RAW_DIR = DR2_DATA_DIR / "raw"
DR2_CACHE_DIR = DR2_DATA_DIR / "cache"
DR2_CURRENT_DIR = DR2_DATA_DIR / "current"

DR3_CONFIG_DIR = DR3_ROOT / "config"
DR3_DATA_DIR = DR3_ROOT / "data"
DR3_SCORES_PATH = DR3_DATA_DIR / "current_scores.json"
