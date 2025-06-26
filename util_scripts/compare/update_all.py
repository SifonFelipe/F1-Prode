from django.db import transaction
from predictions import models as pm
from accounts import models as am
from ranking.models import SeasonScore
from .ranking import update_rankings_and_participations

def apply_updates(updates):
    with transaction.atomic():
        pm.Session.objects.bulk_update(updates["update_session_status"], ['state'])
        pm.Prediction.objects.bulk_update(updates["update_prediction"], ['points_scored'])
        pm.PredictedPosition.objects.bulk_update(updates["update_positions_predictions"], ['correct'])
        pm.PredictedPole.objects.bulk_update(updates["update_poles_predictions"], ['correct'])
        SeasonScore.objects.bulk_update(updates["update_season_scores"], ['points'])
        am.CustomUser.objects.bulk_update(updates["update_user_stats"], ['amount_preds', 'amount_preds_correct', 'best_prediction'])

        update_rankings_and_participations(updates["seasons_compared"])
