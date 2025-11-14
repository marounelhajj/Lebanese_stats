# stats/models.py
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100)
    # Logos uploaded in admin
    logo = models.ImageField(upload_to="team_logos/", blank=True, null=True)

    def __str__(self):
        return self.name


class Player(models.Model):
    POSITION_CHOICES = [
        ("Guard", "Guard"),
        ("Forward", "Forward"),
        ("Center", "Center"),
        ("Guard / Forward", "Guard / Forward"),
        ("Forward / Center", "Forward / Center"),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    number = models.PositiveIntegerField()
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)

    # These MUST match your import_players.py / Excel
    games = models.IntegerField(null=True, blank=True)
    minutes_per_game = models.FloatField(null=True, blank=True)
    points_per_game = models.FloatField(null=True, blank=True)
    rebounds_per_game = models.FloatField(null=True, blank=True)
    assists_per_game = models.FloatField(null=True, blank=True)
    steals_per_game = models.FloatField(null=True, blank=True)
    blocks_per_game = models.FloatField(null=True, blank=True)
    fouls_per_game = models.FloatField(null=True, blank=True)
    turnovers_per_game = models.FloatField(null=True, blank=True)
    two_points_pct = models.FloatField(null=True, blank=True)
    three_points_pct = models.FloatField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.team.name})"
