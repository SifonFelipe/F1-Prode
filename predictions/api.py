from . import models as pm
from django.db.models import Prefetch
from datetime import datetime, timezone
import json

def get_points_system(s_settings, session_type):
    POINTS_MAP = {
        "Race": s_settings.race_points_pred,
        "Sprint": s_settings.sprint_points_pred,
        "Qualifying": {1: s_settings.qualy_points_pred}
    }

    points_system = POINTS_MAP.get(session_type)
    if session_type != "Qualifying":
        points_system = json.loads(points_system) if points_system else {}

    return points_system


def build_results_prefetch(session_type):
    return [
        Prefetch(
            'race_results',
            queryset=pm.Result.objects
            .select_related('driver', 'for_which_team'),
            to_attr='result'
        )
        if session_type != "Qualifying" else
        Prefetch(
            'pole_result',
            queryset=pm.Result.objects
            .select_related('driver', 'for_which_team'),
            to_attr='result'
        )
    ]


def build_predictions_prefetch(user, session_type):
    if session_type == "Qualifying":
        pred_fetch = 'predicted_pole__driver'
    else:
        pred_fetch = 'predicted_positions__driver'

    return [
        Prefetch(
            'predictions',
            queryset=pm.Prediction.objects
            .filter(user__username=user)
            .prefetch_related(pred_fetch),
            to_attr='pred'
        )
    ]


def fetch_full_session_data(season, location, session_type, user=None,
                            include_results=False, include_predictions=False, include_lineup=False):
    session_queryset = (
        pm.Session.objects
        .filter(
            session_type=session_type,
            grand_prix__location=location,
            grand_prix__season__season=season
        )
        .select_related('grand_prix__season')
    )

    if include_lineup:
        session_queryset = session_queryset.prefetch_related(
            Prefetch(
                'drivers',
                queryset=pm.RaceLineUp.objects.select_related('driver'),
                to_attr='lineup'
            )
        )

    if include_results:
        session_queryset = session_queryset.prefetch_related(
            *build_results_prefetch(session_type)
        )

    if include_predictions and user:
        session_queryset = session_queryset.prefetch_related(
            *build_predictions_prefetch(user, session_type)
        )

    return session_queryset.first()


def get_preds(pred):
    pole = list(pred.predicted_pole.all())
    results = list(pred.predicted_positions.all())

    if len(pole) == 1:
        return pole
    else:
        return results


def compare_preds_with_results(pred, results):
    preds = get_preds(pred)
    comparision = {}
    guessed = 0

    for prediction, result in zip(preds, results):
        comparision[prediction] = result

        if prediction.driver == result.driver:
            guessed += 1

    return comparision, guessed


def handle_qualifying_prediction(prediction, positions, created):
    if len(positions) != 1 or '1' not in positions:
        return False
    
    try:
        driver = pm.Driver.objects.get(id=positions['1'])
    except pm.Driver.DoesNotExist:
        return False
    
    pm.PredictedPole.objects.update_or_create(
        prediction=prediction,
        default={'driver': driver}
    )
    return True


def handle_race_or_sprint_prediction(prediction, positions, created, settings):
    if len(positions) != settings.amount_drivers:
        return False
    
    driver_ids = list(positions.values())
    drivers = pm.Driver.objects.in_bulk(driver_ids)

    try:
        predictions = [
            pm.PredictedPosition(
                prediction=prediction,
                driver=drivers[int(driver_id)],
                position=int(pos)
            )

            for pos, driver_id in positions.items()
        ]
    except:
        return False
    
    if not created:
        pm.PredictedPosition.objects.filter(prediction=prediction).delete()

    pm.PredictedPosition.objects.bulk_create(predictions)
    return True


def save_prediction(user, session_id, positions):
    session = (
        pm.Session.objects
        .filter(id=session_id)
        .select_related('grand_prix__season')
    ).first()

    settings = session.grand_prix.season

    if not session or session.session_date < datetime.now(timezone.utc):
        return False

    prediction, created = (
        pm.Prediction.objects
        .get_or_create(
            user=user,
            session=session
        )
    )

    match session.session_type:
        case "Qualifying":
            return handle_qualifying_prediction(prediction, positions, created)
        case "Race" | "Sprint":
            return handle_race_or_sprint_prediction(prediction, positions, created, settings)
        case _:
            return False


def get_teams_and_drivers(season, countdown_ch=False):
    s_settings = (
        pm.SeasonSettings.objects
        .filter(season=season)
        .prefetch_related(
            Prefetch(
                "racing_teams",
                to_attr='teams'
            ),
            Prefetch(
                "drivers",
                to_attr='driversset'
            )
        )
    ).first()

    teams = s_settings.teams
    drivers = s_settings.driversset

    if countdown_ch:
        countdown = s_settings.limit_ch_pred.isoformat()
        return teams, drivers, countdown

    return teams, drivers


def save_champions(request, user, season):
    driver = request['driver_champion']
    team = request['team_champion']

    settings = (
        pm.SeasonSettings.objects
        .filter(season=season)
        .prefetch_related(
            Prefetch(
                "drivers",
                queryset=pm.Driver.objects.filter(id=driver),
                to_attr="driver"
            ),
            Prefetch(
                "racing_teams",
                queryset=pm.RacingTeam.objects.filter(id=team),
                to_attr="team"
            )
        )
    ).first()

    if settings.limit_ch_pred < datetime.now(timezone.utc).date():
        return False
    
    pm.ChampionPrediction.objects.update_or_create(
        user=user,
        season=settings,
        defaults={'driver': settings.driver[0], 'team': settings.team[0]}
    )

    return True