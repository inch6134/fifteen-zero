import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
UCL_COMPETITION_ID = 8

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

STAGE_POINTS = {
    "champion": 10,
    "final": 8,
    "semi": 7,
    "quarter": 5,
    "r16": 3,
    "playoffs": 2,
    "group": 1,
}

POSITION_GROUPS = {
    "GK": "GK",
    "CB": "DEF",
    "LB": "DEF",
    "RB": "DEF",
    "DM": "MID",
    "CM": "MID",
    "AM": "MID",
    "LW": "FWD",
    "RW": "FWD",
    "ST": "FWD",
}

# FBref position codes → our position codes
# Fine-grained distinctions (CB vs LB, DM vs CM) come from position_overrides.json
FBREF_POSITION_MAP = {
    "GK": "GK",
    "DF": "CB",
    "MF": "CM",
    "FW": "ST",
    "DF,MF": "DM",
    "MF,DF": "DM",
    "MF,FW": "AM",
    "FW,MF": "AM",
    "DF,FW": "ST",
}

with open(DATA_DIR / "eras.json") as f:
    ERAS = json.load(f)

with open(DATA_DIR / "clubs.json") as f:
    CLUBS = json.load(f)

# FBref squad name string -> club slug for filtering scraped data
FBREF_NAME_TO_SLUG = {c["fbref_name"]: c["slug"] for c in CLUBS}

with open(DATA_DIR / "ucl_stages.json") as f:
    UCL_STAGES = json.load(f)  # {club_slug: {season_string: stage_string}}

with open(DATA_DIR / "position_overrides.json") as f:
    POSITION_OVERRIDES = json.load(f)  # {fbref_player_id: position_code}
