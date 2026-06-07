from rest_framework import serializers
from .models import Club, Era, ClubEra, PlayerEraStats, GameSession

class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['id', 'name', 'short_name', 'slug', 'country', 'primary_color', 'secondary_color']


class EraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Era
        fields = ['id', 'name', 'start_year', 'end_year']



class ClubEraSerializer(serializers.ModelSerializer):
    club = ClubSerializer(read_only=True)
    era = EraSerializer(read_only=True)

    class Meta:
        model = ClubEra
        fields = ['id', 'club', 'era', 'best_stage', 'ucl_stage_points', 'ucl_seasons', 'ucl_games']


class PlayerEraStatsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='player.name')
    nationality = serializers.CharField(source='player.nationality')
    foot = serializers.CharField(source='player.foot')
    position = serializers.CharField(source='effective_position')

    class Meta:
        model = PlayerEraStats
        fields = [
            'id',
            'name',
            'nationality',
            'foot',
            'position',
            'appearances',
            'minutes',
            'goals',
            'assists',
            'yellow_cards',
            'red_cards',
            'clean_sheets',
            'best_ucl_stage',
            'ucl_stage_points',
            'era_rating',
        ]


class GameSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSession
        fields = ['session_id', 'mode', 'lineup', 'score', 'record', 'grade', 'created_at']
        read_only_fields = ['session_id', 'score', 'record', 'grade', 'created_at']
