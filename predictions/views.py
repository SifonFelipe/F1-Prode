from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Prefetch
from django.utils import timezone

from datetime import datetime, timedelta

import json
from . import api
from F1Prode.static_variables import FNAME_TO_CLASS
from .models import Driver, Session, GrandPrix, Prediction, PredictedPosition, Result, PredictedPole, ResultPole, RacingTeam, ChampionPrediction, SeasonSettings

def createPred(request, season, location, session_type):
    settings, gp, session, lineup, points_system = (
        api.get_gp_sess_lu_and_pts(season, location, session_type)
    )

    position_range = range(1, settings.amount_drivers+1)

    countdown_target = session.session_date.isoformat()

    context = {'drivers': lineup, 'positions_range': position_range, 
            "ABB": FNAME_TO_CLASS, "gp": gp, "session": session,
            "countdown_target": countdown_target, "POINTS": points_system}

    return render(request, "predicts.html", context)


def compare_results(request, user, season, location, session_type):
    gp, session, results, prediction, prediction_preds, points = (
        api.get_sess_results_and_preds(
            location=location,
            season=season,
            session_type=session_type,
            user=user
        )
    )

    comparision_dict, guessed = (
        api.compare_preds_with_results(
            preds=prediction_preds,
            results=results
        )
    )

    points_scored = prediction.points_scored

    context = {
        "gp": gp, "comparision": comparision_dict,
        "guessed": guessed, "points_scored": points_scored,
        "ABB": FNAME_TO_CLASS, "POINTS_SYSTEM": points,
        "session_type": session_type
    }

    return render(request, 'compare_predict.html', context)


def save_pred(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "method wrong"}, status=405)
    try:
        data = json.loads(request.body)
        race_id = data.get("race_id")
        positions = data.get("positions", {})

        if not race_id or not positions:
            return JsonResponse({"success": False, "error": "Incomplete data"}, status=400)

        saved = api.save_prediction(request.user, race_id, positions)

        if saved:
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "invalid JSON"}, status=400)
    
def championPred(request, season):
    teams, drivers, countdown = (
        api.get_teams_and_drivers(season, countdown_ch=True)
    )

    context = {
        "drivers": drivers, "teams": teams,
        "countdown_target": countdown, "range": range(2),
        "season": season
    }
    return render(request, 'champions.html', context)

def saveChampionPred(request, season):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    try:
        if timezone.now() < TIME_LIMIT_CHAMPIONS_PRED:
            team_id = request.POST['team_champion']
            driver_id = request.POST['driver_champion']
            user = request.user
            driver = Driver.objects.get(id=driver_id)
            team = RacingTeam.objects.get(id=team_id)

            pred = ChampionPrediction.objects.filter(user=user, season=season).first()

            if pred:
                pred.team = team
                pred.driver = driver
                pred.save()
            else:
                ChampionPrediction.objects.create(
                    user=user,
                    season=season,
                    team=team,
                    driver=driver
                )

            return redirect('home')
        else:
            return JsonResponse({"success": False, "error": "Out of time"})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)