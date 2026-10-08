from pathlib import Path

# Project Settings

SEASON = "2025-26"
SEASON_TYPE = "Regular Season"
MIN_MINS = 250

# Project Paths

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SEASON_FOLDER = SEASON.replace("-", "_")

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / SEASON_FOLDER
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim" / SEASON_FOLDER
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed" / SEASON_FOLDER
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

FIGURES_DIR = PROJECT_ROOT / "figures"