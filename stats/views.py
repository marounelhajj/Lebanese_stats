from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import Team, Player


# ---------- Helper: build a simple AI-style scouting report ----------

def build_scouting_report(team, players_qs):
    """
    Returns a short scouting report for a given team
    based only on the stats in the database.
    """
    if not players_qs.exists():
        return f"No player data is available yet for {team.name}."

    # Key players
    best_scorer = players_qs.order_by("-points_per_game").first()
    best_rebounder = players_qs.order_by("-rebounds_per_game").first()
    assist_leader = players_qs.order_by("-assists_per_game").first()

    # Team totals / averages
    team_pts = (
        players_qs.aggregate(total=models.Sum("points_per_game"))["total"] or 0
    )
    team_reb = (
        players_qs.aggregate(total=models.Sum("rebounds_per_game"))["total"] or 0
    )
    avg_rating = (
        players_qs.aggregate(avg=models.Avg("rating"))["avg"] or 0
    )

    tempo_phrase = (
        "an up-tempo, offense-first"
        if team_pts >= 80
        else "a more half-court oriented"
    )
    glass_phrase = (
        "strong on the boards"
        if team_reb >= 40
        else "vulnerable on the boards"
    )

    report = (
        f"{team.name} lean heavily on {best_scorer.name} "
        f"({best_scorer.points_per_game:.1f} PPG) as their primary scoring option, "
        f"while {best_rebounder.name} anchors the paint with "
        f"{best_rebounder.rebounds_per_game:.1f} rebounds per game. "
        f"{assist_leader.name} runs the offense and averages "
        f"{assist_leader.assists_per_game:.1f} assists, keeping teammates involved. "
        f"As a group, the team scores around {team_pts:.1f} points and collects "
        f"{team_reb:.1f} rebounds per game, with an average efficiency rating of "
        f"{avg_rating:.1f}. This profile points to {tempo_phrase} squad that is "
        f"{glass_phrase}. To slow them down, opponents should limit early touches for "
        f"{best_scorer.name}, keep {best_rebounder.name} off the glass, and force the "
        f"ball out of {assist_leader.name}'s hands late in possessions."
    )

    return report


# ---------- Main page: list of teams + league leaders ----------

def team_list(request):
    teams = Team.objects.all().order_by("name")
    players = Player.objects.select_related("team").all()

    # League-wide leaders among all players
    best_scorer = players.order_by("-points_per_game").first()
    best_rebounder = players.order_by("-rebounds_per_game").first()
    assist_leader = players.order_by("-assists_per_game").first()

    # Best 2PT% and 3PT% (fractions -> will be *100 in template)
    best_two_pct = (
        players
        .exclude(two_points_pct__isnull=True)
        .order_by("-two_points_pct")
        .first()
    )

    best_three_pct = (
        players
        .exclude(three_points_pct__isnull=True)
        .order_by("-three_points_pct")
        .first()
    )

    context = {
        "teams": teams,
        "best_scorer": best_scorer,
        "best_rebounder": best_rebounder,
        "assist_leader": assist_leader,
        "best_two_pct": best_two_pct,
        "best_three_pct": best_three_pct,
    }
    return render(request, "stats/team_list.html", context)


# ---------- Team detail: logo + scouting report + charts + table ----------

def team_detail(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    players = Player.objects.filter(team=team)

    # Top scorers & rebounders for charts
    top_scorers = players.order_by("-points_per_game")[:5]
    scorers_names = [p.name for p in top_scorers]
    scorers_points = [float(p.points_per_game or 0) for p in top_scorers]

    top_rebounders = players.order_by("-rebounds_per_game")[:5]
    rebound_names = [p.name for p in top_rebounders]
    rebound_values = [float(p.rebounds_per_game or 0) for p in top_rebounders]

    # Pie chart: scoring distribution (top 6 scorers)
    pie_players = players.order_by("-points_per_game")[:6]
    pie_labels = [p.name for p in pie_players]
    pie_values = [float(p.points_per_game or 0) for p in pie_players]

    # AI-style scouting report text
    scouting_report = build_scouting_report(team, players)

    context = {
        "team": team,
        "players": players.order_by("-points_per_game"),
        "scouting_report": scouting_report,
        "scorers_names": scorers_names,
        "scorers_points": scorers_points,
        "rebound_names": rebound_names,
        "rebound_values": rebound_values,
        "pie_labels": pie_labels,
        "pie_values": pie_values,
    }
    return render(request, "stats/team_detail.html", context)


# ---------- Player search with filters ----------

def player_search(request):
    teams = Team.objects.all().order_by("name")
    players = Player.objects.select_related("team").all()

    # Read filter parameters
    team_id = request.GET.get("team_id", "all")
    position = request.GET.get("position", "all")

    def get_float(name):
        val = request.GET.get(name)
        try:
            return float(val) if val not in (None, "",) else None
        except ValueError:
            return None

    params = {
        "min_points": get_float("min_points"),
        "min_rebounds": get_float("min_rebounds"),
        "min_assists": get_float("min_assists"),
        "min_minutes": get_float("min_minutes"),
        "min_rating": get_float("min_rating"),
        "max_fouls": get_float("max_fouls"),
        "min_two_pt": get_float("min_two_pt"),
        "min_three_pt": get_float("min_three_pt"),
    }

    # Apply filters
    if team_id != "all":
        players = players.filter(team_id=team_id)

    if position and position != "all":
        players = players.filter(position=position)

    if params["min_points"] is not None:
        players = players.filter(points_per_game__gte=params["min_points"])

    if params["min_rebounds"] is not None:
        players = players.filter(rebounds_per_game__gte=params["min_rebounds"])

    if params["min_assists"] is not None:
        players = players.filter(assists_per_game__gte=params["min_assists"])

    if params["min_minutes"] is not None:
        players = players.filter(minutes_per_game__gte=params["min_minutes"])

    if params["min_rating"] is not None:
        players = players.filter(rating__gte=params["min_rating"])

    if params["max_fouls"] is not None:
        players = players.filter(fouls_per_game__lte=params["max_fouls"])

    if params["min_two_pt"] is not None:
        players = players.filter(two_points_pct__gte=params["min_two_pt"] / 100.0)

    if params["min_three_pt"] is not None:
        players = players.filter(three_points_pct__gte=params["min_three_pt"] / 100.0)

    players = players.order_by("-rating", "-points_per_game")

    context = {
        "teams": teams,
        "players": players,
        "selected_team_id": team_id,
        "selected_position": position,
        "params": params,
    }
    return render(request, "stats/player_search.html", context)
