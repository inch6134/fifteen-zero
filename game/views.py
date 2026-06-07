import random

from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import ClubEra, PlayerEraStats, GameSession
from .serializers import ClubEraSerializer, PlayerEraStatsSerializer
# from scoring import score_lineup


class IndexView(View):
    def get(self, request):
        return render(request, "index.html")


class HealthView(APIView):
    def get(self, request):
        return Response({"status", "ok"})


class SpinView(APIView):
    def get(self, request):
        exclude_param = request.query_params.get("exclude", "")
        fix_club = request.query_params.get("fix_club")
        fix_era = request.query_params.get("fix_era")

        exclude_ids = [int(i) for i in exclude_param.split(",") if i]

        qs = ClubEra.objects.exclude(id__in=exclude_ids)

        if fix_club:
            qs = qs.filter(club_id=fix_club)
        if fix_era:
            qs = qs.filter(era_id=fix_era)

        ids = list(qs.values_list("id", flat=True))
        if not ids:
            response = Response(
                {"error": "No valid combinations available"}, status=400
            )

        club_era = ClubEra.objects.select_related("club", "era").get(
            id=random.choice(ids)
        )
        response = Response(ClubEraSerializer(club_era).data)

        return response


class PlayerListView(APIView):
    def get(self, request, club_era_id):
        try:
            club_era = ClubEra.objects.select_related("club", "era").get(id=club_era_id)
        except ClubEra.DoesNotExist:
            response = Response({"error": "Not found"}, status=404)

        players = (
            PlayerEraStats.objects.filter(club=club_era.club, era=club_era.era)
            .select_related("player")
            .order_by("-era_rating")
        )
        response = Response(PlayerEraStatsSerializer(players, many=True).data)

        return response


class SessionView(APIView):
    def post(self, request):
        lineup = request.data.get("lineup")  # {slot: player_era_stats_id}
        mode = request.data.get("mode", "classic")

        if not isinstance(lineup, dict) or len(lineup) != 11:
            response = Response(
                {"error": "Lineup must contain exactly 11 players"}, status=400
            )

        stats_ids = list(lineup.values())
        stats_qs = PlayerEraStats.objects.filter(id__in=stats_ids).select_related(
            "player"
        )

        if stats_qs.count() != 11:
            response = Response(
                {"error": "One or more player IDs are invalid"}, status=400
            )

        stats_by_id = {s.id: s for s in stats_qs}

        lineup_data = {
            slot: {
                "id": pid,
                "slot": slot,
                "natural_position": stats_by_id[pid].effective_position,
                "foot": stats_by_id[pid].player.foot,
                "appearances": stats_by_id[pid].appearances,
                "minutes": stats_by_id[pid].minutes,
                "goals": stats_by_id[pid].goals,
                "assists": stats_by_id[pid].assists,
                "yellow_cards": stats_by_id[pid].yellow_cards,
                "red_cards": stats_by_id[pid].red_cards,
                "clean_sheets": stats_by_id[pid].clean_sheets,
                "best_ucl_stage": stats_by_id[pid].best_ucl_stage,
                "ucl_stage_points": stats_by_id[pid].ucl_stage_points,
                "team_ucl_games": stats_by_id[pid].team_ucl_games,
                "era_rating": stats_by_id[pid].era_rating,
            }
            for slot, pid in lineup.items()
        }

        result = score_lineup(lineup_data)

        session = GameSession.objects.create(
            mode=mode,
            lineup=lineup,
            score=result.score,
            record=result.record,
            grade=result.grade,
        )

        response = Response(
            {
                "session_id": str(session.session_id),
                "score": result.score,
                "record": result.record,
                "grade": result.grade,
                "player_scores": result.player_scores,
            }
        )

        return response
