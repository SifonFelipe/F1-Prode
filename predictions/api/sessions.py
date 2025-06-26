from predictions import models as pm
from django.db.models import Prefetch


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
            .filter(season_score__user__username=user)
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
