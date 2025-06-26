from predictions import models as pm
from datetime import datetime, timezone

def handle_qualifying_prediction(prediction, positions):
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
    from ranking import models as rm

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
            season_score=rm.SeasonScore.objects.get(user=user, season=settings),
            session=session
        )
    )

    match session.session_type:
        case "Qualifying":
            return handle_qualifying_prediction(prediction, positions)
        case "Race" | "Sprint":
            return handle_race_or_sprint_prediction(prediction, positions, created, settings)
        case _:
            return False
