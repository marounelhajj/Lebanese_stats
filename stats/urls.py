# stats/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.team_list, name="team_list"),
    path("team/<int:team_id>/", views.team_detail, name="team_detail"),
    path("search/", views.player_search, name="player_search"),
]
