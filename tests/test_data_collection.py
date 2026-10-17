import pandas as pd
import pytest

from nba_archetypes.data_validation import validate_api_data, check_unique_ids
from nba_archetypes.data_collection import (format_shot_locations, save_parquet_file)


def test_duplicate_player_ids():
    df = pd.DataFrame({"PLAYER_ID": [101, 101, 103], "MIN": [1200, 1500, 1800]})
    with pytest.raises(ValueError):
        validate_api_data(df, required_columns=["PLAYER_ID", "MIN"])


def test_missing_required_column():
    df = pd.DataFrame({"PLAYER_ID": [101, 102], "PTS": [20, 15]})
    with pytest.raises(ValueError):
        validate_api_data(df, required_columns=["PLAYER_ID", "MIN"])


def test_check_unique_ids():
    df = pd.DataFrame({"PLAYER_ID": [101, 101, 103]})
    assert check_unique_ids(df, "PLAYER_ID") == False


def test_shot_location_formatting():
    zones = [
        "Restricted Area",
        "In The Paint (Non-RA)",
        "Mid-Range",
        "Left Corner 3",
        "Right Corner 3",
        "Above the Break 3",
        "Backcourt",
    ]

    fake_response = {
        "resultSets": {
            "headers": [
                {"columnNames": zones, "columnsToSkip": 5, "columnSpan": 3},
                {
                    "columnNames": (
                        [
                        "PLAYER_ID", 
                        "PLAYER_NAME",
                        "TEAM_ID",
                        "TEAM_ABBREVIATION",
                        "AGE"
                        ]
                        + ["FGM", "FGA", "FG_PCT"] * 7
                    )
                },
            ],
            "rowSet": [
                [101, "Player A", 1, "AAA", 25] + [1, 2, 0.5] * 7,
                [102, "Player B", 2, "BBB", 26] + [2, 4, 0.5] * 7,
            ],
        }
    }

    result = format_shot_locations(fake_response)

    assert len(result) == 2
    assert result["PLAYER_ID"].tolist() == [101, 102]
    assert result["RA_FGA"].tolist() == [2, 4]


def test_save_parquet_protects_existing_file(tmp_path):
    df = pd.DataFrame({"PLAYER_ID": [101, 102], "PTS": [20, 15]})
    file_path = save_parquet_file(df, "test_stats", tmp_path)
    assert file_path.exists()
    with pytest.raises(FileExistsError):
        save_parquet_file(df, "test_stats", tmp_path)
    saved_df = pd.read_parquet(file_path)
    pd.testing.assert_frame_equal(saved_df, df)