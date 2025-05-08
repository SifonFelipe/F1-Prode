from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Prefetch

from datetime import datetime, timezone, timedelta

import json

from .models import Driver, Session, GrandPrix, Prediction, PredictedPosition, Result, PredictedPole, ResultPole

FNAME_TO_CLASS = {
    "Red Bull Racing": "red-bull",
    "Racing Bulls": "racing-bulls",
    "Haas F1 Team": "haas",
    "Kick Sauber": "sauber",
    "Williams": "williams",
    "Mercedes": "mercedes",
    "McLaren": "mclaren",
    "Ferrari": "ferrari",
    "Aston Martin": "aston-martin",
    "Alpine": "alpine"
}

POINTS_BY_POSITION = {
    1: 5,
    2: 3,
    3: 2,
    4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    11: 0.5, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5,
    16: 0.25, 17: 0.25, 18: 0.25, 19: 0.25, 20: 0.25
}

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
                'sessions',  # usá el related_name correcto
                queryset=Session.objects.filter(session_type=session_type, grand_prix__location=location, grand_prix__year=year),
                to_attr='session'
            )
        )
    ).first()

    drivers = Driver.objects.all()[:20]
    position_range = [x for x in range(1, 21)]
    session = gp.session[0]

    now = datetime.now(timezone.utc)
    remaining = session.session_date - now

    if remaining < timedelta(0):
        remaining_time = "¡Tiempo finalizado"
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


def save_pred(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            print(data)

            race_id = data.get("race_id")
            positions = data.get("positions", {})

            if not race_id or not positions:
                return JsonResponse({"success": False, "error": "Datos incompletos"}, status=400)

            session = Session.objects.get(id=race_id)
            prediction, pred_created = Prediction.objects.get_or_create(user=request.user, session=session)

            """
            now = datetime.now(timezone.utc)
            remaining = session.session_date - now
            
            if remaining < timedelta(0):
                return JsonResponse({"success": False, "error": "Out of time"})
            """

            if session.session_type == "Qualifying":
                if len(positions) != 1:
                    return JsonResponse({"success": False, "error": "not enough data"})
                
                pole, created = PredictedPole.objects.get_or_create(prediction=prediction)
                
                print(positions['1'])
                driver = Driver.objects.get(id=positions['1'])

                if not created:
                    pole.driver=driver
                    pole.save()
                else:
                    PredictedPole.objects.create(
                        prediction=prediction,
                        driver=driver,
                    )

                print(f"Guardando: Qualy {race_id} - 1 - Piloto {driver.last_name}")

            elif session.session_type == "Race":
                if len(positions) != 20:
                    return JsonResponse({"success": False, "error": "not enough data"})

                if not pred_created:
                    try:
                        PredictedPosition.objects.filter(prediction=prediction).delete()
                    except:
                        None

                for pos, driver_id in positions.items():
                    driver = Driver.objects.get(id=driver_id)
                    
                    PredictedPosition.objects.create(
                        prediction=prediction,
                        driver=driver,
                        position=int(pos)
                    )

                    print(f"Guardando: Carrera {race_id} - Pos {pos}: Piloto {driver_id}")  # DEBUG

            return JsonResponse({"success": True})
        
        except json.JSONDecodeError:
            if not created:
                try:
                    PredictedPosition.objects.filter(prediciton=prediction).delete()
                except:
                    None
            return JsonResponse({"success": False, "error": "JSON inválido"}, status=400)
        
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

def compare_results(request, year, location, session_type):
    gp = GrandPrix.objects.get(year=int(year), location=location)
    session = Session.objects.get(grand_prix=gp, session_type=session_type)
    predictions_user = Prediction.objects.get(user=request.user, session=session)

    if session_type == "Qualifying":
        results = ResultPole.objects.filter(session=session)
        predictions = PredictedPole.objects.filter(prediction=predictions_user)
    else:
        results = Result.objects.filter(session=session)    
        predictions = PredictedPosition.objects.filter(prediction=predictions_user)

    comparision = {}
    guessed = 0

    for prediction, result in zip(predictions, results):
        comparision[prediction] = result

        if prediction.driver == result.driver:
            guessed += 1

    context = {"gp": gp, "comparision": comparision, "ABB": FNAME_TO_CLASS, "POINTS_SYSTEM": POINTS_BY_POSITION,
                "guessed": guessed, "points_scored": predictions_user.points_scored}
    return render(request, 'compare_predict.html', context)