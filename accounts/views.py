from django.shortcuts import render
from django.db.models import Count, Q

from .models import CustomUser
from ranking.models import YearScore
from predictions.models import Prediction, GrandPrix

from datetime import datetime

year = datetime.now().year

from django.shortcuts import get_object_or_404

def profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)
    year = datetime.now().year

    scores = list(YearScore.objects.filter(user=profile_user))
    score_actual_year = next((s for s in scores if s.year == year), None)
    best_season = scores[0] if scores else None

    predictions = list(
        Prediction.objects
        .filter(user=profile_user, session__grand_prix__ended=True) #ended to not count other ones
        .select_related('session__grand_prix')
        .prefetch_related('predicted_positions__driver', 'predicted_pole__driver')
    )

    best_score = predictions[0] if predictions else None
    season_predictions = [
        p for p in predictions
        if p.session.grand_prix.year == year and p.session.session_type == "Race"
    ]
    
    best_season_score = max(season_predictions, key=lambda p: p.points_scored, default=None)

    #counters
    amount_guessed = amount_wrong = amount_races = 0
    for prediction in predictions:
        if prediction.session.session_type == "Race":
            amount_races += 1

        for pos in prediction.predicted_positions.all():
            if pos.correct:
                amount_guessed += 1
            else:
                amount_wrong += 1

    amount_points = sum((score.points for score in scores), start=0)
    average_points = float(amount_points / amount_races) if amount_races else 0

    races_counts = (
        GrandPrix.objects
        .filter(year=year)
        .aggregate(
            total_races=Count('id'),
            races_completed=Count('id', filter=Q(ended=True))
        )
    )

    
    gps = races_counts['total_races']
    gps_ended = races_counts['races_completed']

    percentage_season = (gps_ended / gps) * 100 if gps else 0
    percentage_participation = (len(season_predictions) / gps_ended) * 100 if gps_ended else 0
    average_guess = (amount_guessed / (amount_guessed + amount_wrong)) * 100 if (amount_guessed+amount_wrong) else 0

    context = {
        "profile_user": profile_user,
        "score": score_actual_year,
        "best_season": best_season,
        "best_score": predictions[0] if predictions else None,
        "best_season_score": best_season_score,
        "amount_races": amount_races,
        "amount_guessed": amount_guessed,
        "amount_points": amount_points,
        "average_points": round(average_points, 2),
        "percentage_season": round(percentage_season, 2),
        "participation": round(percentage_participation, 2),
        "average_guess": round(average_guess, 2),
    }

    return render(request, "profile.html", context)