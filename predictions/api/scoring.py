import json


def get_points_system(s_settings, session_type, return_complete=False):
    POINTS_MAP = {
        "Race": s_settings.race_points_pred,
        "Sprint": s_settings.sprint_points_pred,
        "Qualifying": {1: s_settings.qualy_points_pred}
    }

    if return_complete:
        POINTS_MAP["Race"] = json.loads(POINTS_MAP["Race"])
        POINTS_MAP["Sprint"] = json.loads(POINTS_MAP["Sprint"])
        return POINTS_MAP

    points_system = POINTS_MAP.get(session_type)
    if session_type != "Qualifying":
        points_system = json.loads(points_system) if points_system else {}

    return points_system


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
