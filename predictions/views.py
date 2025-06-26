from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from . import api
from F1Prode.static_variables import FNAME_TO_CLASS


def createPred(request, season, location, session_type):
    session = api.fetch_full_session_data(
        season=season,
        location=location,
        session_type=session_type,
        user=request.user,
        include_lineup=True
    )

    settings = session.grand_prix.season
    drivers = [line.driver for line in session.lineup]
    points_system = api.get_points_system(settings, session_type)

    position_range = range(1, settings.amount_drivers+1)
    countdown_target = session.session_date.isoformat()

    context = {'drivers': drivers, 'positions_range': position_range, 
            "ABB": FNAME_TO_CLASS, "gp": session.grand_prix, "session": session,
            "countdown_target": countdown_target, "POINTS": points_system}

    return render(request, "predicts.html", context)


def compare_results(request, user, season, location, session_type):
    session = api.fetch_full_session_data(
        season=season,
        location=location,
        session_type=session_type,
        user=user,
        include_results=True,
        include_predictions=True
    )

    pred = session.pred[0]
    points_scored = pred.points_scored
    settings = session.grand_prix.season
    points = api.get_points_system(settings, session_type)

    comparision_dict, guessed = (
        api.compare_preds_with_results(
            pred=pred,
            results=session.result
        )
    )

    context = {
        "gp": session.grand_prix, "comparision": comparision_dict,
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
        session_id = data.get("race_id")
        positions = data.get("positions", {})

        if not session_id or not positions:
            return JsonResponse({"success": False, "error": "Incomplete data"}, status=400)

        saved = api.save_prediction(
            user=request.user,
            session_id=session_id, 
            positions=positions
        )

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
        saved = api.save_champions(
            request=request.POST,
            user=request.user,
            season=season
        )

        if saved:
            #return redirect('home')
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
