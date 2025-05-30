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


def compare_preds_with_results(preds, results):
    comparision = {}
    guessed = 0

    for prediction, result in zip(preds, results):
        comparision[prediction] = result

        if prediction.driver == result.driver:
            guessed += 1

    return comparision, guessed


def get_gp_sess_lu_and_pts(season, location, session_type):
    s_settings = (
        pm.SeasonSettings.objects
        .filter(season=season)
        .prefetch_related(
            Prefetch(
                "gps",
                queryset=pm.GrandPrix.objects
                .filter(location=location)
                .prefetch_related(
                    Prefetch(
                        "sessions",
                        queryset=pm.Session.objects
                        .filter(session_type=session_type)
                        .prefetch_related('drivers'),
                        to_attr='session'
                    )
                ),
                to_attr='gp'
            )
        )
    ).first()

    points_system = get_points_system(s_settings, session_type)

    gp = s_settings.gp[0]
    session = gp.session[0]

    lineups = []
    for lineup in session.drivers.all():
        lineups.append(lineup.driver)

    return s_settings, gp, session, lineups, points_system


def get_sess_results_and_preds(location, season, session_type, user):
    if session_type == "Qualifying":
        pred_fetch = 'predicted_pole__driver'
    else:
        pred_fetch = 'predicted_positions__driver'

    s_settings = pm.SeasonSettings.objects.get(season=season)

    session = (
        pm.Session.objects
        .filter(
            grand_prix__location=location,
            grand_prix__season=s_settings,
            session_type=session_type
        )
        .select_related('grand_prix')
        .prefetch_related(
            Prefetch(
                'predictions',
                queryset=pm.Prediction.objects
                .filter(user__username=user)
                #.select_related('user')
                .prefetch_related(pred_fetch),
                to_attr='pred'
            ),
            Prefetch(
                'race_results',
                queryset=pm.Result.objects
                .select_related('driver', 'for_which_team'),
                to_attr='results'
            ),

            Prefetch(
                'pole_result',
                queryset=pm.ResultPole.objects
                .select_related('driver', 'for_which_team'),
                to_attr='result'
            )
        )
    ).first()

    points_system = get_points_system(s_settings, session_type)
    gp = session.grand_prix
    prediction = session.pred[0]

    if session_type == "Qualifying":
        results = session.result
        prediction_preds = prediction.predicted_pole.all()
    else:
        results = session.results
        prediction_preds = prediction.predicted_positions.all()

    return gp, session, results, prediction, prediction_preds, points_system


def save_prediction(user, session_id, positions):
    session = (
        pm.Session.objects
        .filter(id=session_id)
        .select_related('grand_prix__season')
    ).first()

    s_settings = session.grand_prix.season

    prediction, created = (
        pm.Prediction.objects
        .get_or_create(
            user=user,
            session=session
        )
    )

    now = datetime.now(timezone.utc)
    if session.session_date < now:
        return False

    session_type = session.session_type

    if session_type == "Qualifying":
        if len(positions) != 1:
            return False
        
        driver = pm.Driver.objects.get(id=positions['1'])
        pm.PredictedPole.objects.update_or_create(
            prediction=prediction,
            defaults={'driver': driver}
        )

    elif session_type == "Race" or session_type == "Sprint":
        if len(positions) != s_settings.amount_drivers:
            return False
        
        if not created:
            pm.PredictedPosition.objects.filter(
                prediction=prediction
            ).delete()

        driver_ids = list(positions.values())
        drivers = pm.Driver.objects.in_bulk(driver_ids)

        preds = [
            pm.PredictedPosition(
                prediction=prediction,
                driver=drivers[int(driver_id)],
                position=int(pos)
            )
            for pos, driver_id in positions.items()
        ]

        pm.PredictedPosition.objects.bulk_create(preds)

    return True


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

    if countdown:
        countdown = s_settings.limit_ch_pred.isoformat()
        return teams, drivers, countdown

    return teams, drivers