from . import models as acc_models
from django.db.models import Sum, Prefetch
from ranking import models as rank_models

def get_user_and_season_scores(username):
    user = (
        acc_models.CustomUser.objects
        .filter(username=username)
        .select_related('best_prediction')
        .prefetch_related(
            Prefetch(
                'season_scores',
                queryset=rank_models.SeasonScore.objects.prefetch_related(
                    Prefetch("predictions", to_attr="s_predictions")
                ),
                to_attr='seasons'
            )
        )
        .annotate(
            total_races=Sum('season_scores__gps_participated'),
            total_points=Sum('season_scores__points')
        )
        .first()
    )

    if user:
        return user
    else:
        return None


def create_user_data_dict(user, current_season, ended_gps):
    amount_races = user.total_races or 0
    amount_points = user.total_points or 0

    season_scores = user.seasons

    actual_season = next((s for s in season_scores if s.season == current_season), None)
    season_predictions = actual_season.s_predictions
    best_season_prediction = season_predictions[0]
    participations = actual_season.gps_participated
    avg_participation = (
        (participations / ended_gps) * 100
        if ended_gps else 0
    )

    best_season = season_scores[0]
    best_prediction = user.best_prediction

    amount_pos_preds = user.amount_preds
    amount_guessed = user.amount_preds_correct
    amount_wrong = amount_pos_preds - amount_guessed

    avg_guess = (amount_guessed / amount_pos_preds)

    user_data = {
        "user": user,
        "amount_races": amount_races,
        "amount_points": round(amount_points, 2),
        "actual_season": actual_season,
        "best_season_prediction": best_season_prediction,
        "participations": {
            "actual_season": participations,
            "avg_actual_season": round(avg_participation, 2)
        },
        "best_season": best_season,
        "best_prediction": best_prediction,
        "preds": {
            "total": amount_pos_preds,
            "guessed": amount_guessed,
            "wrong": amount_wrong,
            "avg_guess": round(avg_guess, 2)
        }
    }

    return user_data
