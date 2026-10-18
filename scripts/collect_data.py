import argparse
from nba_archetypes.config import SEASON, SEASON_TYPE
from nba_archetypes.data_collection import(
    get_player_stats,
    get_tracking_stats,
    get_shot_location_stats,
    get_hustle_stats,
    get_matchup_stats
)


def main():
    parser = argparse.ArgumentParser(description="Collect NBA player statistics.")

    parser.add_argument(
        "--dataset", 
        required=True, 
        choices=[
            "players",
            "tracking",
            "shot_locations",
            "hustle",
            "matchups",
            "all"
        ],
        help = "Choose which data to collect."
    )

    parser.add_argument(
        "--force",
        action = "store_true",
        help = "Download fresh data and overwrite existing files."
    )

    args = parser.parse_args()
    print(f"Collecting {SEASON} {SEASON_TYPE} data.")

    if args.dataset in ("players", "all"):
        get_player_stats(force=args.force)

    if args.dataset in ("tracking", "all"):
        get_tracking_stats(force=args.force)

    if args.dataset in ("shot_locations", "all"):
        get_shot_location_stats(force=args.force)

    if args.dataset in ("hustle", "all"):
        get_hustle_stats(force=args.force)

    if args.dataset in ("matchups", "all"):
        get_matchup_stats(force=args.force)

    print("Data collection completed successfully.")


if __name__ == "__main__":
    main()