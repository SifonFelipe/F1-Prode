from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Prefetch

from datetime import datetime, timezone, timedelta

import json

from F1Prode.static_variables import DRIVERS_BY_RACE, FNAME_TO_CLASS, PRED_POINTS_BY_POSITION
from .models import Driver, Session, GrandPrix, Prediction, PredictedPosition, Result, PredictedPole, ResultPole

def createPred(request, year, location, session_type):
    location.capitalize()
    session_type.capitalize()

    # LATER create line-up model for each race for situations when
    # there aren't the same 20 drivers as before
    # so you will get session.lineup (for example) to drivers
    gp = (
        GrandPrix.objects
        .filter(year=year, location=location)
        .prefetch_related(
            Prefetch(
                'sessions',  # related_name
                queryset=Session.objects.filter(session_type=session_type, grand_prix__location=location, grand_prix__year=year),
                to_attr='session'
            )
        )
    ).first()

    drivers = Driver.objects.filter(year=year)[:DRIVERS_BY_RACE]
    position_range = [x for x in range(1, DRIVERS_BY_RACE+1)]
    session = gp.session[0]

    now = datetime.now(timezone.utc)
    remaining = session.session_date - now

    if remaining < timedelta(0):
        remaining_time = "¡Tiempo finalizado!"
    else:
        amount_seconds = int(remaining.total_seconds())

        hours, rest = divmod(amount_seconds, 3600)
        minutes, seconds = divmod(rest, 60)

        remaining_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    context = {'drivers': drivers, 'positions_range': position_range, "ABB": FNAME_TO_CLASS, "gp": gp, 
               "session": session, "remaining_time": remaining_time}
    
    if session_type == "Qualifying":
        return render(request, "pole_predicts.html", context)

    return render(request, "predicts.html", context)

def compare_results(request, user, year, location, session_type):
    
    session = (
        Session.objects
        .filter(grand_prix__location=location, grand_prix__year=int(year), session_type=session_type)
        .select_related('grand_prix')
        .prefetch_related(
            Prefetch(
                'predictions',
                queryset=Prediction.objects.filter(user__username=user).select_related('user').prefetch_related(
                    'predicted_positions__driver',
                    'predicted_pole__driver',
                )
            ),

            Prefetch(
                'race_results',
                queryset=Result.objects.select_related('driver', 'for_which_team')
            ),

            Prefetch(
                'pole_result',
                queryset=ResultPole.objects.select_related('driver', 'for_which_team')
            )
        )
    ).first()
    
    gp = session.grand_prix
    predictions_user = session.predictions.all().first()
    prediction = session.predictions.all().first()

    if session_type == "Qualifying":
        results = session.pole_result.all()
        predictions = prediction.predicted_pole.all()
    else:
        results = session.race_results.all()    
        predictions = prediction.predicted_positions.all()

    comparision = {}
    guessed = 0

    for prediction, result in zip(predictions, results):
        comparision[prediction] = result

        if prediction.driver == result.driver:
            guessed += 1

    context = {"gp": gp, "comparision": comparision, "ABB": FNAME_TO_CLASS, "POINTS_SYSTEM": PRED_POINTS_BY_POSITION,
                "guessed": guessed, "points_scored": predictions_user.points_scored, "session_type": session_type}
    return render(request, 'compare_predict.html', context)

def save_pred(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        race_id = data.get("race_id")
        positions = data.get("positions", {})

        if not race_id or not positions:
            return JsonResponse({"success": False, "error": "Datos incompletos"}, status=400)

        session = Session.objects.get(id=race_id)
        prediction, pred_created = Prediction.objects.get_or_create(user=request.user, session=session)

        now = datetime.now(timezone.utc)
        if session.session_date < now:
            return JsonResponse({"success": False, "error": "Out of time"})

        if session.session_type == "Qualifying":
            if len(positions) != 1:
                return JsonResponse({"success": False, "error": "not exact data"})

            driver = Driver.objects.get(id=positions['1'])
            pole, _ = PredictedPole.objects.get_or_create(prediction=prediction)
            pole.driver = driver
            pole.save()

        elif session.session_type == "Race":
            if len(positions) != DRIVERS_BY_RACE:
                return JsonResponse({"success": False, "error": "not enough data"})

            if not pred_created:
                PredictedPosition.objects.filter(prediction=prediction).delete()

            driver_ids = list(positions.values())
            drivers = Driver.objects.in_bulk(driver_ids)

            predicted_positions = [
                PredictedPosition(
                    prediction=prediction,
                    driver=drivers[int(driver_id)],
                    position=int(pos)
                )
                for pos, driver_id in positions.items()
            ]

            PredictedPosition.objects.bulk_create(predicted_positions)

        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)