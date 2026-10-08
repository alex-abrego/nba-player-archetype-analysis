from pathlib import Path

# Project Settings

SEASON = "2025-26"
SEASON_TYPE = "Regular Season"
MIN_MINS = 250

# Project Paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "2025_26"
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim" / "2025_26"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed" / "2025_26"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

FIGURES_DIR = PROJECT_ROOT / "figures"