"""
Scrapes UCL player stats from FBref via soccerdata.

Raw CSVs are cached in pipeline/data/raw. Delete a file to force a re-scrape.
"""

import time
import soccerdata as sd
from config import RAW_DIR

UCL_LEAGUE = "INT-Champions League"
SEASONS = list(range(1992, 2026))
REQUEST_DELAY = 5  # keep at 5+ to respect FBref rate limits


def scrape_season(end_year: int):
    season_label = f"{end_year - 1}-{end_year}"
    std_path = RAW_DIR / f"{season_label}_standard.csv"
    gk_path = RAW_DIR / f"{season_label}_keepers.csv"

    if std_path.exists() and gk_path.exists():
        return

    reader = sd.FBref(leagues=UCL_LEAGUE, seasons=int(end_year))

    if not std_path.exists():
        reader.read_player_season_stats(stat_type="standard").to_csv(std_path)
        time.sleep(REQUEST_DELAY)

    if not gk_path.exists():
        reader.read_player_season_stats(stat_type="keeper").to_csv(gk_path)
        time.sleep(REQUEST_DELAY)


def scrape_all():
    print(f"Scraping {len(SEASONS)} UCL seasons (cached seasons are skipped)...")
    for end_year in SEASONS:
        print(f"    {end_year - 1}-{end_year}", end=" ", flush=True)
        try:
            scrape_season(end_year)
            print("✓")
        except Exception as e:
            print(f"✗  ({e})")


if __name__ == "__main__":
    scrape_all()
