from django.shortcuts import render
from django.db.models import Prefetch

from predictions.models import Driver, GrandPrix, Session, Prediction, Result
from ranking.models import YearScore

import requests
from datetime import datetime

year = datetime.now().year

def home(request):
    """
    Next feature --> add models apart of each circuit with extra data.
    """

    next_gp = GrandPrix.objects.filter(year=2025, ended=False).select_related(None).first()
    next_race = (
        Session.objects
        .select_related('grand_prix')
        .get(grand_prix=next_gp, session_type="Race")
    ) 
    countdown_target_race = next_race.session_date

    prev_gps = (
        GrandPrix.objects
        .filter(year=year, ended=True)
        .order_by("-date")
        .prefetch_related(
            Prefetch(
                "sessions",
                queryset=Session.objects.filter(session_type="Race").prefetch_related(
                    Prefetch(
                        "race_results",
                        queryset=Result.objects.select_related("driver").filter(position=1),
                        to_attr="first_place_result"
                    ),
                    Prefetch(
                        "predictions",
                        queryset=Prediction.objects.select_related("user").order_by("points_scored"),
                        to_attr="best_preds"
                    )
                )
            )
        )[:3]
    )

    gps_data = []
    for gp in prev_gps:
        race_session = next((s for s in gp.sessions.all() if s.session_type == "Race"), None)
        winner = race_session.first_place_result[0].driver if race_session and race_session.first_place_result else None
        best_prediction = race_session.best_preds[0] if race_session and race_session.predictions else None

        gps_data.append({
            "gp": gp,
            "winner": winner,
            "best_prediction": best_prediction
        })

    ranking = (
        YearScore.objects
        .filter(year=year)
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "user__prediction_set",
                queryset=Prediction.objects.filter(session__grand_prix__ended=True)
                .select_related("session__grand_prix")
                .order_by("-session__grand_prix__date"),
                to_attr="recent_predictions"
            )
        )[:5]
    )

    ranking_dict = {}
    for score in ranking:
        user_preds = score.user.recent_predictions
        last_score = user_preds[0].points_scored if user_preds else 0
        ranking_dict[score] = last_score

    context = {
        "next_race": next_race,
        "next_gp": next_gp,
        "countdown_target": countdown_target_race,
        "ranking": ranking_dict,
        "gps_data": gps_data
    }
    return render(request, "home.html", context)
