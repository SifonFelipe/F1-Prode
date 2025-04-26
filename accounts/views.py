from django.shortcuts import render
from django.db.models import Sum

from .models import CustomUser
from ranking.models import YearScore
from predictions.models import Prediction, GrandPrix

from datetime import datetime

year = datetime.now().year

from django.shortcuts import get_object_or_404

def profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    year = datetime.now().year

    scores = YearScore.objects.filter(user=profile_user)
    score_actual_year = scores.filter(year=year).first()
    best_season = scores.first()

    predictions = Prediction.objects.filter(user=profile_user).select_related('session__grand_prix')
    best_score = predictions.first()
    season_predictions = predictions.filter(session__grand_prix__year=year)
    best_season_score = season_predictions.first()

    amount_races = profile_user.amount_races
    amount_guessed = profile_user.amount_guessed
    amount_wrong = profile_user.amount_wrong
    amount_points = profile_user.total_points
    average_points = float(amount_points / amount_races) if amount_races else 0

    gps = GrandPrix.objects.filter(year=year).count()
    gps_ended = GrandPrix.objects.filter(year=year, ended=True).count()
    percentage_season = (gps_ended / gps) * 100 if gps else 0
    percentage_participation = (len(season_predictions) / gps_ended) * 100 if gps_ended else 0
    average_guess = (amount_guessed / (amount_guessed+amount_wrong)) * 100 if (amount_guessed+amount_wrong) else 0

    context = {
        "profile_user": profile_user,
        "score": score_actual_year,
        "best_season": best_season,
        "best_score": best_score,
        "best_season_score": best_season_score,
        "amount_races": amount_races,
        "amount_guessed": amount_guessed,
        "amount_points": amount_points,
        "average_points": average_points,
        "percentage_season": percentage_season,
        "participation": percentage_participation,
        "average_guess": average_guess,
    }

    return render(request, "profile.html", context)