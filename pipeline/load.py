"""
UPSERTs processed CSV data into the Django PostgreSQL database.
Table names follow Django's convention: game_<modelname_lowercase>.
Run after transform.py has produced files in pipeline/data/processed/.
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from config import DATABASE_URL, PROCESSED_DIR, ERAS, CLUBS


def connect():
    return psycopg2.connect(DATABASE_URL)


def load_clubs(cur):
    execute_values(cur, """
        INSERT INTO game_club (name, short_name, slug, country, league, primary_color, secondary_color, fbref_id)
        VALUES %s
        ON CONFLICT (slug) DO UPDATE SET
            name            = EXCLUDED.name,
            short_name      = EXCLUDED.short_name,
            primary_color   = EXCLUDED.primary_color,
            secondary_color = EXCLUDED.secondary_color,
            fbref_id        = EXCLUDED.fbref_id
    """, [(
        c['name'], c.get('short_name', c['name']), c['slug'], c['country'], c['league'],
        c.get('primary_color', '#000000'), c.get('secondary_color', '#FFFFFF'), c['fbref_id']
    ) for c in CLUBS])

    cur.execute("SELECT id, slug FROM game_club")
    return {row[1]: row[0] for row in cur.fetchall()}


def load_eras(cur):
    execute_values(cur, """
        INSERT INTO game_era (id, name, start_year, end_year)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            name       = EXCLUDED.name,
            start_year = EXCLUDED.start_year,
            end_year   = EXCLUDED.end_year
    """, [(e['id'], e['name'], e['start_year'], e['end_year']) for e in ERAS])

    cur.execute("SELECT id FROM game_era")
    return {row[0] for row in cur.fetchall()}


def load_club_eras(cur, club_ids):
    df = pd.read_csv(PROCESSED_DIR / 'club_eras.csv')
    rows = []
    for _, row in df.iterrows():
        club_id = club_ids.get(row['club_slug'])
        if not club_id:
            continue
        rows.append((
            club_id, int(row['era_id']), int(row['ucl_seasons']),
            int(row['ucl_games']), row['best_stage'], int(row['ucl_stage_points']),
        ))
    execute_values(cur, """
        INSERT INTO game_clubera (club_id, era_id, ucl_seasons, ucl_games, best_stage, ucl_stage_points)
        VALUES %s
        ON CONFLICT (club_id, era_id) DO UPDATE SET
            ucl_seasons      = EXCLUDED.ucl_seasons,
            ucl_games        = EXCLUDED.ucl_games,
            best_stage       = EXCLUDED.best_stage,
            ucl_stage_points = EXCLUDED.ucl_stage_points
    """, rows)


def load_players(cur, df):
    rows = [(row['player_name'], row.get('nationality', ''), row['position'], '', '') 
            for _, row in df.drop_duplicates('player_name').iterrows()]
    execute_values(cur, """
        INSERT INTO game_player (name, nationality, position, foot, fbref_id)
        VALUES %s
        ON CONFLICT (fbref_id) DO UPDATE SET
            name        = EXCLUDED.name,
            nationality = EXCLUDED.nationality,
            position    = EXCLUDED.position
    """, rows)
    # Note: fbref_id is blank here — the pipeline doesn't scrape player profile IDs.
    # Players are matched by name. This works for the MVP but means the unique
    # constraint on fbref_id will conflict if the same name appears twice with
    # different fbref_ids. Refine by scraping player profile pages if needed.

    cur.execute("SELECT id, name FROM game_player")
    return {row[1]: row[0] for row in cur.fetchall()}


def load_player_era_stats(cur, df, club_ids, player_ids):
    rows = []
    for _, row in df.iterrows():
        club_id   = club_ids.get(row['club_slug'])
        player_id = player_ids.get(row['player_name'])
        if not club_id or not player_id:
            continue
        rows.append((
            player_id, club_id, int(row['era_id']),
            row['position'], int(row['appearances']), int(row['minutes']),
            int(row['goals']), int(row['assists']),
            int(row['yellow_cards']), int(row['red_cards']), int(row['clean_sheets']),
            row['best_ucl_stage'], int(row['ucl_stage_points']),
            int(row['team_ucl_games']), float(row['era_rating']) if pd.notna(row['era_rating']) else None,
        ))
    execute_values(cur, """
        INSERT INTO game_playererastats
            (player_id, club_id, era_id, position, appearances, minutes,
             goals, assists, yellow_cards, red_cards, clean_sheets,
             best_ucl_stage, ucl_stage_points, team_ucl_games, era_rating)
        VALUES %s
        ON CONFLICT (player_id, club_id, era_id) DO UPDATE SET
            appearances      = EXCLUDED.appearances,
            minutes          = EXCLUDED.minutes,
            goals            = EXCLUDED.goals,
            assists          = EXCLUDED.assists,
            yellow_cards     = EXCLUDED.yellow_cards,
            red_cards        = EXCLUDED.red_cards,
            clean_sheets     = EXCLUDED.clean_sheets,
            best_ucl_stage   = EXCLUDED.best_ucl_stage,
            ucl_stage_points = EXCLUDED.ucl_stage_points,
            team_ucl_games   = EXCLUDED.team_ucl_games,
            era_rating       = EXCLUDED.era_rating
    """, rows)


def load_all():
    df = pd.read_csv(PROCESSED_DIR / 'player_era_stats.csv')

    with connect() as conn:
        with conn.cursor() as cur:
            print('Loading clubs...')
            club_ids = load_clubs(cur)

            print('Loading eras...')
            load_eras(cur)

            print('Loading club eras...')
            load_club_eras(cur, club_ids)

            print('Loading players...')
            player_ids = load_players(cur, df)

            print('Loading player era stats...')
            load_player_era_stats(cur, df, club_ids, player_ids)

        conn.commit()
    print('Done.')


if __name__ == '__main__':
    load_all()
