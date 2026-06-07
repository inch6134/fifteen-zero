# 15-0: Build an invincible Champions League Starting XI

```
fifteen-zero/
│
├── config/                          # Django project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py              # Picks dev or prod based on DJANGO_ENV
│   │   ├── base.py                  # Shared: installed apps, DRF, templates, static
│   │   ├── dev.py                   # SQLite, DEBUG=True, local vars
│   │   └── prod.py                  # Postgres via DATABASE_URL, whitenoise, ALLOWED_HOSTS
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── game/                            # Core Django app 
│   ├── __init__.py
│   ├── admin.py                     # Register all models
│   ├── models.py                    # Club, Era, Player, PlayerEraStats, GameSession
│   ├── views.py                     # Spin, Players, Sessions endpoints + index view
│   ├── urls.py
│   ├── serializers.py
│   └── migrations/
│       └── __init__.py
│
├── templates/
│   └── index.html                   # Single-page app shell, loads Alpine + static JS
│
├── static/
│   ├── css/
│   │   └── main.css
│   └── js/
│       ├── game.js                  # Alpine.js x-data component: full game state
│       ├── slot.js                  # Slot machine animation logic
│       └── ui.js                    # Helpers: share card, dark mode, modals
│
├── pipeline/                        # Standalone data pipeline
│   ├── requirements.txt             # fbrefdata, psycopg2-binary, python-dotenv, pandas
│   ├── .env.example                 # DATABASE_URL only
│   ├── config.py                    # Era windows, club slugs, FBref competition ID (8)
│   ├── scrape.py                    # fbrefdata → raw DataFrames per season
│   ├── transform.py                 # Aggregate by era, compute percentile ratings
│   ├── load.py                      # UPSERT into Postgres via psycopg2
│   ├── run.py                       # Entry point: python run.py [--club=] [--era=]
│   └── data/
│       ├── clubs.json               # Curated club list with slugs + FBref IDs
│       ├── eras.json                # Era window definitions
│       ├── raw/                     # gitignored — scraped CSVs
│       └── processed/               # gitignored — transformed, ready to load
│
├── manage.py
├── requirements.txt                 # Django, DRF, psycopg2, whitenoise, gunicorn, scoring pkg
├── Procfile                         # web: gunicorn config.wsgi --workers 2
├── railway.toml
├── .env.example
├── .gitignore
└── README.md
```
