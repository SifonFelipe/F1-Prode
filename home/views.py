from django.shortcuts import render

from predictions.models import Driver, GrandPrix, Session, Prediction, Result
from ranking.models import YearScore

import requests
from datetime import datetime

year = datetime.now().year

def home(request):
    """
    Next feature --> add models apart of each circuit with extra data.
    """
    next_gp = GrandPrix.objects.filter(year=2025, ended=False).first()
    next_race = Session.objects.get(grand_prix=next_gp, session_type="Race")
    countdown_target_race = next_race.session_date

    prev_gps = GrandPrix.objects.filter(year=year, ended=True).order_by("-date")[:3]

    gps_data = []
    for gp in prev_gps:
        result = Result.objects.get(session__grand_prix=gp, position=1)
        winner = result.driver if result else None

        best_prediction = Prediction.objects.filter(session__grand_prix=gp).select_related('user').first()

        gps_data.append({
            "gp": gp,
            "winner": winner,
            "best_prediction": best_prediction
        })

    ranking = YearScore.objects.filter(year=year)[:5]

    ranking_dict = {}
    for score in ranking:
        last_score = Prediction.objects.filter(session__grand_prix__ended=True, user=score.user).order_by("-session__grand_prix__date").first()
        ranking_dict[score] =  last_score.points_scored if last_score else 0


    context = {"next_race": next_race, "next_gp": next_gp, "countdown_target": countdown_target_race, "ranking": ranking_dict,
               "gps_data": gps_data}
    return render(request, "home.html", context)
