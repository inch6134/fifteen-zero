import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.environ['DATABASE_URL']
UCL_COMPETITION_ID = 8

DATA_DIR = Path(__file__).parent / 'data'

with open(DATA_DIR / 'eras.json') as f:
    ERAS = json.load(f)

with open(DATA_DIR / 'clubs.json') as f:
    CLUBS = json.load(f)
