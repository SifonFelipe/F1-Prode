from .sessions_processing import process_sessions
from .update_all import apply_updates
from predictions import models as pm
from django.db.models import Prefetch

def get_sessions_to_compare():
    sessions_to_fetch = ["Race", "Sprint", "Qualifying"]
    sessions_to_compare = (
        pm.Session.objects
        .filter(state="FWC", session_type__in=sessions_to_fetch)
        .select_related('grand_prix', 'grand_prix__season')
        .prefetch_related(
            Prefetch(
                'predictions',
                queryset=pm.Prediction.objects
                .select_related('season_score', 'season_score__user')
                .prefetch_related(
                    'predicted_positions__driver',
                    'predicted_pole__driver'
                ),
                to_attr='preds'
            ),
            Prefetch(
                'race_results',
                queryset=pm.Result.objects
                .select_related('driver', 'for_which_team'),
                to_attr="results"
            ),
            Prefetch(
                'pole_result',
                queryset=pm.ResultPole.objects
                .select_related('driver', 'for_which_team'),
                to_attr="pole"
            )
        )
    )

    return sessions_to_compare

def main():
    sessions = get_sessions_to_compare()
    updates = process_sessions(sessions)
    apply_updates(updates)

if __name__ == "__main__":
    main()
