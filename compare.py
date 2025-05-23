from predictions.models import Session, Result, Prediction, PredictedPosition, PredictedPole, ResultPole, SeasonSettings
from ranking.models import YearScore
from django.db.models import Prefetch, Count
from decimal import Decimal
import json


def update_rankings_and_participations(seasons, users):
    """
    Using a ranking field on the model to not have to make a query
    of all the scores everytime you want to know the position of a
    user. The same reason with participations.
    """

    for season in seasons:
        scores_update = []
        scores = YearScore.objects.filter(season=season).order_by('-points')
        for i, score in enumerate(scores, start=1):
            score.position = i
            scores_update.append(score)

        # counting different gps
        season_obj = SeasonSettings.objects.get(season=season)
        predictions_per_season = (
            Prediction.objects
            .filter(user__season_scores__in=users, session__grand_prix__season=season_obj)
            .values("user__season_scores__id", "session__grand_prix__season")
            .annotate(gp_count=Count('session__grand_prix', distinct=True))
        )

        to_update = {
            pred['user__season_scores__id']: pred['gp_count']
            for pred in predictions_per_season
        }

        # filter from the scores objects previously filtered
        scores = scores.filter(id__in=to_update.keys())

        for score in scores:
            score.gps_participated = to_update[score.id]

        YearScore.objects.bulk_update(scores, ['gps_participated'])
        YearScore.objects.bulk_update(scores_update, ['position'])


def race_results_list(session):
    """
    Creates a list with the results of the session, in order.
    """
    drivers_positions = []

    for result in session.race_results.all():
        drivers_positions.append(result.driver.number)

    return drivers_positions


def compare_preds_update_db(session, result_data, score_format, season, mode='Race'):
    """
    Generalized function to process predictions
    - mode: 'Race' (or 'Sprint') for positional predictions,
      'Qualifying' for pole prediction.
    - result_data: list of driver numbers (for race) or single
      result object (for qualy).
    """

    updated_preds = []
    updated_ys = []
    updated_correct_objs = []
    user_set = set()

    for prediction in session.predictions.all():

        # year_score is used to update the user score at the end
        year_score = year_scores_dict[(prediction.user_id, season)]
        points = 0

        if mode == 'Race' or mode == 'Sprint':
            predicted_positions = prediction.predicted_positions.all()
            for idx, predicted_position in enumerate(predicted_positions):
                if result_data[idx] == predicted_position.driver.number:
                    key = str(idx + 1)
                    points += score_format[key]
                    predicted_position.correct = True
                    updated_correct_objs.append(predicted_position)

        elif mode == 'Qualifying':
            pole_pred = prediction.predicted_pole.all().first()
            if pole_pred.driver == result_data.driver:
                points += score_format
                pole_pred.correct = True
                updated_correct_objs.append(pole_pred)

        if points > 0:
            prediction.points_scored += Decimal(str(points))
            year_score.points += Decimal(str(points))

            updated_preds.append(prediction)
            updated_ys.append(year_score)

        user_set.add(year_score)

    Prediction.objects.bulk_update(updated_preds, ['points_scored'])
    YearScore.objects.bulk_update(updated_ys, ['points'])

    if mode == 'race':
        PredictedPosition.objects.bulk_update(updated_correct_objs, ['correct'])
    elif mode == 'qualy':
        PredictedPole.objects.bulk_update(updated_correct_objs, ['correct'])

    return user_set


# big query to fetch all the data to use at the moment of comparing
sessions_to_fetch = ["Race", "Sprint", "Qualifying"]
sessions_to_compare = (
    Session.objects
    .filter(state="FWC", session_type__in=sessions_to_fetch)
    .select_related('grand_prix', 'grand_prix__season')
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

sessions_to_update = []  # Sessions to update state from FWC to F
last_setting = 0  # Check when settings change
seasons = []  # Seasons list to iterate when changing rankings and participations
users = set()  # Users set to change gps participations
all_settings = SeasonSettings.objects.all()  # Settings from all the years

for session in sessions_to_compare:
    session_type = session.session_type
    session_season = session.grand_prix.season.season

    print(f"\nComparing Results and Predictions of\n{session_type} - {session.grand_prix.name}")

    #  Check if the season settings change and changes it if it does
    if last_setting != session_season:
        last_setting = session_season
        settings = all_settings.get(season=session_season)

        scores_formats = {
            "Race": json.loads(settings.race_points_pred),
            "Sprint": json.loads(settings.sprint_points_pred),
            "Qualifying": settings.qualy_points_pred,
        }

        yearscores = YearScore.objects.filter(season=session_season)
        year_scores_dict = {(ys.user_id, ys.season): ys for ys in yearscores}

        seasons.append(session_season)

    score_format = scores_formats[session_type]
    if session_type == "Race" or session_type == "Sprint":
        result = race_results_list(session)

    elif session_type == "Qualifying":
        result = session.pole_result.all().first()

    users_set = compare_preds_update_db(session, result, score_format, session_season, mode=session_type)
    users = users.union(users_set)

    session.state = "F"
    sessions_to_update.append(session)

    print("Done!")

Session.objects.bulk_update(sessions_to_update, ['state'])

update_rankings_and_participations(seasons, users)

names = set(x.grand_prix.name for x in sessions_to_update)
print(f"Users who predicted:\n{users}\nSessions compared:\n{names}")
