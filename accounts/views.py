from django.shortcuts import render
from F1Prode.static_variables import CURRENT_SEASON
from predictions import api as predictions_api
from . import api as accounts_api

def calculate_percentage(x, y):
    return (x / y) * 100 if y else 0

def profile(request, username):
    total_gps, ended_gps = predictions_api.season_gps_status(CURRENT_SEASON)
    percentage_season =  calculate_percentage(ended_gps, total_gps)

    user = accounts_api.get_user_and_season_scores(username=username)

    if not user:
        return None
    
    user_data = accounts_api.create_user_data_dict(
        user=user, current_season=CURRENT_SEASON, ended_gps=ended_gps
    )

    context = user_data
    context["percentage_season"] = percentage_season

    return render(request, "profile.html", context)