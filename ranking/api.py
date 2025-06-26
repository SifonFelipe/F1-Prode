from accounts import models as acc_models
from . import models as rank_models
from django.db.models import Q, Prefetch

def get_user_and_friends_with_score(user, season):
    friends_and_user = (
        acc_models.CustomUser.objects
        .filter(
            Q(received_requests__from_user=user, received_requests__is_accepted=True) |
            Q(sent_requests__to_user=user, sent_requests__is_accepted=True) |
            Q(username=user)
        )
        .prefetch_related(
            Prefetch(
                "season_scores",
                queryset=rank_models.SeasonScore.objects.filter(season=season),
                to_attr="actual_season_score"
            )
        )
    )

    return friends_and_user


def get_season_scores(season):
    scores = (
        rank_models.SeasonScore.objects
        .filter(season=season)
        .select_related('user')
        .order_by('-points')
    )

    return scores