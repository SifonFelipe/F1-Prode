from predictions.models import Session, Result, Prediction, PredictedPosition, PredictedPole, ResultPole
from ranking.models import YearScore

from django.db.models import Prefetch, Count

from datetime import datetime
from decimal import Decimal

from F1Prode.static_variables import PRED_POINTS_BY_POSITION, PRED_POLE_POINTS, SPRINT_PRED_POINTS_BY_POSITION, CURRENT_SEASON

users = set()

def update_rankings(season):
    scores = YearScore.objects.filter(season=season).order_by('-points')
    for i, score in enumerate(scores, start=1):
        score.position = i
        score.save()

def create_race_results_comparing_list(session):
    drivers_positions = []

    for result in session.race_results.all():
        drivers_positions.append(result.driver.number)

    return drivers_positions


yearscores = YearScore.objects.filter(season=CURRENT_SEASON)
year_scores_dict = {(ys.user_id, ys.season): ys for ys in yearscores}

def compare_race_predictions_and_update(session, drivers_positions, SCORE_FORMAT):
    updated_preds = []
    updated_ys = []
    updated_pred_pos = []
    user_set = set()

    for prediction in session.predictions.all():
        predicted_positions = prediction.predicted_positions.all()

        points = 0
        
        for idx, predicted_position in enumerate(predicted_positions):
            if drivers_positions[idx] == predicted_position.driver.number:
                points += SCORE_FORMAT[idx+1]
                predicted_position.correct = True
                
                updated_pred_pos.append(predicted_position)

        year_score = year_scores_dict[(prediction.user_id, CURRENT_SEASON)]
        if points != 0:
            prediction.points_scored += Decimal(str(points))
            year_score.points += Decimal(str(points))

            updated_preds.append(prediction)
            updated_ys.append(year_score)

        user_set.add(year_score)

    Prediction.objects.bulk_update(updated_preds, ['points_scored'])
    YearScore.objects.bulk_update(updated_ys, ['points'])
    PredictedPosition.objects.bulk_update(updated_pred_pos, ['correct'])

    return user_set


def compare_qualy_predictions_and_update(session, pole_result):
    updated_preds = []
    updated_ys = []
    updated_pred_pole = []
    user_set = set()

    for prediction in session.predictions.all():
        pole_pred = prediction.predicted_pole.all().first()

        if pole_pred.driver == pole_result.driver:
            year_score = year_scores_dict[(prediction.user_id, CURRENT_SEASON)]

            prediction.points_scored += PRED_POLE_POINTS
            year_score.points += PRED_POLE_POINTS
            pole_pred.correct = True

            updated_preds.append(prediction)
            updated_ys.append(year_score)
            updated_pred_pole.append(pole_pred)

            user_set.add(year_score)

    Prediction.objects.bulk_update(updated_preds, ['points_scored'])
    YearScore.objects.bulk_update(updated_ys, ['points'])
    PredictedPole.objects.bulk_update(updated_pred_pole, ['correct'])

    return user_set

sessions_to_compare = (
    Session.objects
    .filter(state="FWC")
    .select_related('grand_prix')
    .prefetch_related(
        Prefetch(
            'predictions',
            queryset=Prediction.objects.select_related('user').prefetch_related(
                'predicted_positions__driver',
                'predicted_pole__driver'
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
)

sessions_to_update = []
for session in sessions_to_compare:
    session_type = session.session_type
    print(f"\nComparing Results and Predictions of\n{session_type} - {session.grand_prix.name}")
    
    if session_type == "Race" or "Sprint":
        drivers_positions = create_race_results_comparing_list(session)

        score_format = PRED_POINTS_BY_POSITION if session_type == "Race" else SPRINT_PRED_POINTS_BY_POSITION
        users_set = compare_race_predictions_and_update(session, drivers_positions, score_format)
        users = users.union(users_set)

    elif session_type == "Qualifying":
        result = session.pole_result.all().first()
        users_set = compare_qualy_predictions_and_update(session, result)
        users = users.union(users_set)

    session.state = "F"
    sessions_to_update.append(session)

    print("Done!")

Session.objects.bulk_update(sessions_to_update, ['state'])

update_rankings(CURRENT_SEASON)

#update gps_participated to have a fast access to them
predictions_per_season = (
    Prediction.objects
    .filter(user__season_scores__in=users, session__grand_prix__season=CURRENT_SEASON)
    .values("user__season_scores__id", "session__grand_prix__season")
    .annotate(gp_count=Count('session__grand_prix', distinct=True))
)

to_update = {
    pred['user__season_scores__id']: pred['gp_count']
    for pred in predictions_per_season
}

scores = YearScore.objects.filter(id__in=to_update.keys())

for score in scores:
    score.gps_participated = to_update[score.id]

YearScore.objects.bulk_update(scores, ['gps_participated'])