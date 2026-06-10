import uuid
from django.db import models

ISO_COUNTRY_CODE_LENGTH = 3  # ISO 3166-1 alpha-3 country codes
HEX_CODE_LENGTH = 7  # eg. '#ffffff'
FBREF_CODE_LENGTH = 8  # eg. 206d90db
ERA_NAME_LENGTH = 9  # eg. '2009-2014'


UCL_STAGES = [
    ("champion", "Champion"),
    ("final", "Finalist"),
    ("semi", "Semi-Finals"),
    ("quarter", "Quarter-Finals"),
    ("r16", "Round of 16 / Group Stage 2"),
    ("playoffs", "Knockout Playoffs"),
    ("group", "Group Stage / League Phase"),
]

POSITIONS = [
    ("GK", "Goalkeeper"),
    ("CB", "Center-back"),
    ("LB", "Left-back"),
    ("RB", "Right-back"),
    ("DM", "Defensive Midfielder"),
    ("CM", "Central Midfielder"),
    ("AM", "Attacking Midfielder"),
    ("LW", "Left Winger"),
    ("RW", "Right Winger"),
    ("ST", "Striker"),
]

FEET = [
    ("L", "Left"),
    ("R", "Right"),
    ("B", "Both"),
]


class Club(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)
    country = models.CharField(max_length=ISO_COUNTRY_CODE_LENGTH)
    primary_color = models.CharField(max_length=HEX_CODE_LENGTH)
    secondary_color = models.CharField(max_length=HEX_CODE_LENGTH)
    fbref_id = models.CharField(max_length=FBREF_CODE_LENGTH, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Era(models.Model):
    name = models.CharField(max_length=ERA_NAME_LENGTH)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["start_year"]


class ClubEra(models.Model):
    """
    Represents a club's UCL participation across an era window.
    The spin/ endpoint draws from this table:
    Only valid club + era combinations that have player data will be included.
    """

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="club_eras")
    era = models.ForeignKey(Era, on_delete=models.CASCADE, related_name="club_eras")
    ucl_seasons = models.PositiveSmallIntegerField(
        default=0
    )  # seasons qualified in this era
    ucl_games = models.PositiveSmallIntegerField(default=0)  # total games played
    best_stage = models.CharField(max_length=10, choices=UCL_STAGES)
    ucl_stage_points = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.club.short_name} ({self.era.name})"

    class Meta:
        unique_together = ("club", "era")
        ordering = ["club__name", "era__start_year"]


class Player(models.Model):
    name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=50)
    position = models.CharField(max_length=2, choices=POSITIONS)
    foot = models.CharField(max_length=1, choices=FEET, blank=True)
    fbref_id = models.CharField(max_length=FBREF_CODE_LENGTH, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class PlayerEraStats(models.Model):
    player = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="era_stats"
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="era_stats")
    era = models.ForeignKey(Era, on_delete=models.CASCADE, related_name="player_stats")

    # Positional override for this era (e.g. Pirlo as DM vs earlier career as CM).
    # Empty means: use player.position.
    position = models.CharField(max_length=2, choices=POSITIONS, blank=True)

    # Raw stats aggregated across all UCL appearances in the era window
    appearances = models.PositiveSmallIntegerField(default=0)
    minutes = models.PositiveIntegerField(default=0)
    goals = models.PositiveSmallIntegerField(default=0)
    assists = models.PositiveSmallIntegerField(default=0)
    yellow_cards = models.PositiveSmallIntegerField(default=0)
    red_cards = models.PositiveSmallIntegerField(default=0)
    clean_sheets = models.PositiveSmallIntegerField(default=0)

    # Best UCL stage this player reached with this club during the era.
    # May differ from ClubEra.best_stage if they weren't present for every season.
    best_ucl_stage = models.CharField(max_length=10, choices=UCL_STAGES)
    ucl_stage_points = models.PositiveSmallIntegerField(default=0)

    # Total UCL games the club played across the era window while this player was in the squad.
    # Used by the scoring module to compute participation rate (minutes / team_ucl_games × 90).
    team_ucl_games = models.PositiveSmallIntegerField(default=0)

    # Percentile rating (0–100) within position group and era, written by the pipeline.
    # Null until the pipeline has run.
    era_rating = models.FloatField(null=True, blank=True)

    @property
    def effective_position(self):
        return self.position or self.player.position

    def __str__(self):
        return f"{self.player.name} – {self.club.short_name} ({self.era.name})"

    class Meta:
        unique_together = ("player", "club", "era")
        ordering = ["-era_rating"]


class GameSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(
        max_length=10,
        choices=[
            ("classic", "Classic"),
            ("ball", "Ball Knowledge"),
        ],
        default="classic",
    )

    # {slot: player_era_stats_id}, e.g. {'GK': 42, 'LB': 17, 'CB_1': 33, 'CB_2': 58, ...}
    lineup = models.JSONField()

    score = models.FloatField(null=True, blank=True)
    record = models.CharField(max_length=4, blank=True)  # e.g. '15-0', '13-2'
    grade = models.CharField(max_length=2, blank=True)  # e.g. 'S+', 'A'

    def __str__(self):
        return f"{self.session_id} — {self.record} ({self.grade})"

    class Meta:
        ordering = ["-created_at"]
