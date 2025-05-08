from predictions.models import Session, Result, Prediction, PredictedPosition, PredictedPole, ResultPole
from ranking.models import YearScore

from django.db.models import Prefetch

from datetime import datetime

POINTS_BY_POSITION_RACE = {
    1: 5,
    2: 3,
    3: 2,
    4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    11: 0.5, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5,
    16: 0.25, 17: 0.25, 18: 0.25, 19: 0.25, 20: 0.25
}

now = datetime.now()
year = now.year

def update_rankings(year):
    scores = YearScore.objects.filter(year=year).order_by('-points')
    for i, score in enumerate(scores, start=1):
        score.position = i
        score.save()

def create_race_results_comparing_list(session):
    drivers_positions = []

    for result in session.result_set.all():
        drivers_positions.append(result.driver.number)

    return drivers_positions


yearscores = YearScore.objects.filter(year=year)
year_scores_dict = {(ys.user_id, ys.year): ys for ys in yearscores}

def compare_race_predictions_and_update(session, drivers_positions):
    updated_preds = []
    updated_ys = []
    updated_pred_pos = []

    for prediction in session.prediction_set.all():
        predicted_positions = prediction.predicted_positions.all()

        points = 0
        
        for idx, predicted_position in enumerate(predicted_positions):
            if drivers_positions[idx] == predicted_position.driver.number:
                points += POINTS_BY_POSITION_RACE[idx+1]
                predicted_position.correct = True
                
                updated_pred_pos.append(predicted_position)

        if points != 0:
            year_score = year_scores_dict[(prediction.user_id, year)]

            prediction.points_scored += points
            year_score.points += points

            updated_preds.append(prediction)
            updated_ys.append(year_score)

    Prediction.objects.bulk_update(updated_preds, ['points_scored'])
    YearScore.objects.bulk_update(updated_ys, ['points'])
    PredictedPosition.objects.bulk_update(updated_pred_pos, ['correct'])


def compare_qualy_predictions_and_update(session, pole_result):
    updated_preds = []
    updated_ys = []
    updated_pred_pole = []

    for prediction in session.prediction_set.all():
        pole_pred = prediction.predicted_pole.all().first()
        
        if pole_pred.driver == pole_result.driver:
            year_score = year_scores_dict[(prediction.user_id, year)]

            prediction.points_scored += 4
            year_score.points += 4
            pole_pred.correct = True

            updated_preds.append(prediction)
            updated_ys.append(year_score)
            updated_pred_pole.append(pole_pred)

    Prediction.objects.bulk_update(updated_preds, ['points_scored'])
    YearScore.objects.bulk_update(updated_ys, ['points'])
    PredictedPole.objects.bulk_update(updated_pred_pole, ['correct'])

sessions_to_compare = (
    Session.objects
    .filter(state="FWC")
    .select_related('grand_prix')
    .prefetch_related(
        Prefetch(
            'prediction_set',
            queryset=Prediction.objects.select_related('user').prefetch_related(
                'predicted_positions__driver',
                'predicted_pole__driver'
            )
        ),

        Prefetch(
            'result_set',
            queryset=Result.objects.select_related('driver', 'for_which_team')
        ),

        Prefetch(
            'resultpole_set',
            queryset=ResultPole.objects.select_related('driver', 'for_which_team')
        )

    )
)


for session in sessions_to_compare:
    session_type = session.session_type
    print(f"\nComparing Results and Predictions of\n{session_type} - {session.grand_prix.name}")
    
    if session_type == "Race":
        drivers_positions = create_race_results_comparing_list(session)
        compare_race_predictions_and_update(session, drivers_positions)

    elif session_type == "Qualifying":
        result = session.resultpole_set.all().first()
        compare_qualy_predictions_and_update(session, result)

    print("\nDone!\n")

update_rankings(year)