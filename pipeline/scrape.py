"""
Scrapes UCL player stats from FBref via soccerdata.

Raw CSVs are cached in pipeline/data/raw. Delete a file to force a re-scrape.
"""

import time
import soccerdata as sd
from config import RAW_DIR

UCL_LEAGUE      = 'INT-European Championship'
SEASONS         = [f"{y}-{y+1}" for y in range (1992, 2026)]
REQUEST_DELAY   = 5 # keep at 5+ to respect FBref rate limits


def scrape_season(season: str):
    std_path = RAW_DIR / f"{season}_standard.csv"
    gk_path = RAW_DIR / f"{season}_keepers.csv"

    if std_path.exists() and gk_path.exists():
        return
 
    reader = sd.FBref(leagues=UCL_LEAGUE, seasons=season)

    if not std_path.exists():
        df = reader.read_player_season_stats(stat_type='standard')
        df = df.reset_index()  # moves league/season/team/player into regular columns
        df.columns = ['_'.join(filter(None, col)).strip() if isinstance(col, tuple) else col
              for col in df.columns]
        df.to_csv(std_path, index=False) 
        time.sleep(REQUEST_DELAY)

    if not gk_path.exists():
        df = reader.read_player_season_stats(stat_type='keeper')
        df = df.reset_index()  # moves league/season/team/player into regular columns
        df.columns = ['_'.join(filter(None, col)).strip() if isinstance(col, tuple) else col
              for col in df.columns]
        df.to_csv(std_path, index=False) 
        time.sleep(REQUEST_DELAY)


def scrape_all():
    print(f"Scraping {len(SEASONS)} UCL seasons (cached seasons are skipped)...")
    for season in SEASONS:
        print(f"    {season}", end=' ', flush=True)
        try:
            scrape_season(season)
            print('✓')
        except Exception as e:
            print(f"✗  ({e})")


if __name__=='__main__':
    scrape_all()
