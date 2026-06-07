from django.contrib import admin
from .models import Club, Era, ClubEra, Player, PlayerEraStats, GameSession

admin.site.register(Club)
admin.site.register(Era)
admin.site.register(ClubEra)
admin.site.register(Player)
admin.site.register(PlayerEraStats)
admin.site.register(GameSession)
