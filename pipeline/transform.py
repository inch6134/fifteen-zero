"""
Aggregates raw per-season FBref data into per-era player stats.

If normalization fails with a KeyError, the column names from soccerdata
don't match the expected mapping. Run the following to inspect actual columns:
    import pandas as pd
    df = pd.read_csv('data/raw/2022-2023_standard.csv')
    print(df.columns.tolist())
Then update STANDARD_COL_MAP and KEEPERS_COL_MAP accordingly.
"""

import pandas as pd
from config import (
    FBREF_NAME_TO_SLUG,
    POSITION_GROUPS,
    PROCESSED_DIR,
    RAW_DIR,
    ERAS,
    POSITION_OVERRIDES,
    FBREF_POSITION_MAP,
    STAGE_GAMES,
    STAGE_POINTS,
    UCL_STAGES,
    CLUBS,
)

STANDARD_COL_MAP = {
    "player": "player_name",
    "team": "squad",
    "nation": "nationality",
    "pos": "fbref_pos",
    # Stat columns — may be prefixed after column flattening
    "MP": "appearances",
    "Playing_Time_MP": "appearances",
    "Min": "minutes",
    "Playing_Time_Min": "minutes",
    "Gls": "goals",
    "Performance_Gls": "goals",
    "Ast": "assists",
    "Performance_Ast": "assists",
    "CrdY": "yellow_cards",
    "Performance_CrdY": "yellow_cards",
    "CrdR": "red_cards",
    "Performance_CrdR": "red_cards",
}
KEEPERS_COL_MAP = {
    "player": "player_name",
    "squad": "squad",
    "games": "appearances",
    "clean_sheets": "clean_sheets",
    "gk_clean_sheets": "clean_sheets",
    "Player": "player_name",
    "Squad": "squad",
    "MP": "appearances",
    "CS": "clean_sheets",
}

REQUIRED_STANDARD = [
    "player_name",
    "squad",
    "fbref_pos",
    "appearances",
    "minutes",
    "goals",
    "assists",
]
MIN_APPEARANCES = 1
STAGE_ORDER = ["champion", "final", "semi", "quarter", "r16", "playoffs", "group"]


def season_start_year(season: int) -> int:
    if isinstance(season, (int, float)):
        return int(season) - 1  # 1993 → 1992
    parts = str(season).split("-")
    return int(parts[0])  # "1992-1993" or "1992-93" → 1992


def get_era(start_year: int) -> dict | None:
    returned_era = None
    for era in ERAS:
        if era["start_year"] <= start_year < era["end_year"]:
            returned_era = era

    return returned_era


def normalize(df: pd.DataFrame, col_map: dict, required: list[str]) -> pd.DataFrame:
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()

    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing after normalization: {missing} | Actual: {df.columns.tolist()}"
        )

    return df


def load_all_seasons() -> tuple[pd.DataFrame, pd.DataFrame]:
    std_frames, gk_frames = [], []

    for path in sorted(RAW_DIR.glob("*_standard.csv")):
        season = path.stem.replace("_standard", "")
        df = normalize(pd.read_csv(path), STANDARD_COL_MAP, REQUIRED_STANDARD)
        df["season"] = season
        std_frames.append(df)

    for path in sorted(RAW_DIR.glob("*_keepers.csv")):
        season = path.stem.replace("_keepers", "")
        df = normalize(pd.read_csv(path), KEEPERS_COL_MAP, ["player_name", "squad"])
        df["season"] = season
        if "clean_sheets" not in df.columns:
            df["clean_sheets"] = 0
        gk_frames.append(df[["player_name", "squad", "season", "clean_sheets"]])

    return pd.concat(std_frames, ignore_index=True), pd.concat(
        gk_frames, ignore_index=True
    )


def resolve_position(fbref_pos: str, player_name: str) -> str:
    # position_overrides.json uses player names as keys since FBref IDs
    # may not be available in all season table rows
    if player_name in POSITION_OVERRIDES:
        return POSITION_OVERRIDES[player_name]
    return FBREF_POSITION_MAP.get(str(fbref_pos).strip(), "CM")


def ucl_stage_stats(club_slug: str, seasons: list[str]) -> dict:
    history = UCL_STAGES.get(club_slug, {})
    stages, points, games = [], 0, 0
    for season in seasons:
        stage = history.get(season)
        if not stage:
            continue
        stages.append(stage)
        points += STAGE_POINTS.get(stage, 0)
        base = 8 if season_start_year(season) >= 2024 else 6
        games += base + STAGE_GAMES.get(stage, 0)
        games += 2 if season_start_year(season) >= 2024 else 0  # knockout playoffs
    best = min(stages, key=lambda s: STAGE_ORDER.index(s)) if stages else "group"
    return {"best_ucl_stage": best, "ucl_stage_points": points, "team_ucl_games": games}


def raw_score(row: pd.Series) -> float:
    mins = row["minutes"]
    per90 = max(mins / 90, 1)
    apps = row["appearances"]
    group = row["position_group"]
    score = 0.0

    if group == "GK":
        score = row["clean_sheets"] / apps if apps > 0 else 0.0
    if group == "DEF":
        cs_rate = row["clean_sheets"] / apps if apps > 0 else 0.0
        score = 0.6 * cs_rate + 0.4 * (row["goals"] + row["assists"]) / per90
    if group == "MID":
        score = (row["goals"] + row["assists"]) / per90
    if group == "FWD":
        score = (0.6 * row["goals"] + 0.4 * row["assists"]) / per90

    return score


def transform():
    print("Loading raw season data...")
    std_df, gk_df = load_all_seasons()

    std_df["club_slug"] = std_df["squad"].map(FBREF_NAME_TO_SLUG)
    std_df = std_df[std_df["club_slug"].notna()].copy()

    std_df["start_year"] = std_df["season"].apply(season_start_year)
    std_df["era"] = std_df["start_year"].apply(get_era)
    std_df = std_df[std_df["era"].notna()].copy()
    std_df["era_id"] = std_df["era"].apply(lambda e: e["id"])
    std_df["era_name"] = std_df["era"].apply(lambda e: e["name"])

    std_df["position"] = std_df.apply(
        lambda r: resolve_position(r["fbref_pos"], r["player_name"]), axis=1
    )
    std_df["position_group"] = std_df["position"].map(POSITION_GROUPS)

    std_df = std_df.merge(
        gk_df.rename(columns={"squad": "squad"}),
        on=["player_name", "squad", "season"],
        how="left",
    )
    std_df["clean_sheets"] = std_df["clean_sheets"].fillna(0).astype(int)

    GROUP_KEYS = [
        "player_name",
        "club_slug",
        "era_id",
        "era_name",
        "position",
        "position_group",
    ]

    agg = (
        std_df.groupby(GROUP_KEYS)
        .agg(
            appearances=("appearances", "sum"),
            minutes=("minutes", "sum"),
            goals=("goals", "sum"),
            assists=("assists", "sum"),
            yellow_cards=("yellow_cards", "sum"),
            red_cards=("red_cards", "sum"),
            clean_sheets=("clean_sheets", "sum"),
            nationality=("nationality", "first"),
            seasons=("season", list),
        )
        .reset_index()
    )

    agg = agg[agg["appearances"] >= MIN_APPEARANCES].copy()

    stage_cols = agg.apply(
        lambda r: ucl_stage_stats(r["club_slug"], r["seasons"]),
        axis=1,
        result_type="expand",
    )
    agg = pd.concat([agg, stage_cols], axis=1)

    agg["raw_score"] = agg.apply(raw_score, axis=1)
    agg["era_rating"] = (
        agg.groupby(["position_group", "era_id"])["raw_score"]
        .rank(pct=True)
        .mul(100)
        .round(1)
    )

    club_era_rows = []
    for club in CLUBS:
        history = UCL_STAGES.get(club["slug"], {})
        for era in ERAS:
            era_seasons = {
                s: st
                for s, st in history.items()
                if era["start_year"] <= season_start_year(s) < era["end_year"]
            }
            if not era_seasons:
                continue
            stages = list(era_seasons.values())
            best = min(stages, key=lambda s: STAGE_ORDER.index(s))
            points = sum(STAGE_POINTS[s] for s in stages)
            games = sum(
                (8 if season_start_year(s) >= 2024 else 6)
                + STAGE_GAMES[st]
                + (2 if season_start_year(s) >= 2024 and st == "playoffs" else 0)
                for s, st in era_seasons.items()
            )
            club_era_rows.append(
                {
                    "club_slug": club["slug"],
                    "era_id": era["id"],
                    "era_name": era["name"],
                    "ucl_seasons": len(era_seasons),
                    "ucl_games": games,
                    "best_stage": best,
                    "ucl_stage_points": points,
                }
            )

    pd.DataFrame(club_era_rows).to_csv(PROCESSED_DIR / "club_eras.csv", index=False)

    output_cols = [
        "player_name",
        "nationality",
        "position",
        "club_slug",
        "era_id",
        "appearances",
        "minutes",
        "goals",
        "assists",
        "yellow_cards",
        "red_cards",
        "clean_sheets",
        "best_ucl_stage",
        "ucl_stage_points",
        "team_ucl_games",
        "era_rating",
    ]
    agg[output_cols].to_csv(PROCESSED_DIR / "player_era_stats.csv", index=False)

    print(
        f"Done: {len(agg)} player-era records, {len(club_era_rows)} club-era combinations"
    )


if __name__ == "__main__":
    transform()
