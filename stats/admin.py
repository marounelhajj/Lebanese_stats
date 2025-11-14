# stats/admin.py
from django.contrib import admin
from .models import Team, Player


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "team",
        "number",
        "position",
        "games",
        "minutes_per_game",
        "points_per_game",
        "rebounds_per_game",
        "assists_per_game",
        "steals_per_game",
        "blocks_per_game",
        "fouls_per_game",
        "turnovers_per_game",
        "two_points_pct",
        "three_points_pct",
        "rating",
    )
    list_filter = ("team", "position")
    search_fields = ("name",)
