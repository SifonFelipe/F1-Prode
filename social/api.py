from social import models as social_models
from ranking import models as rank_models

def get_league(username, leaguename):
    league = (
        social_models.PrivateLeague.objects
        .filter(name=leaguename, creator__username=username)
        .prefetch_related("members__season_scores")
        .first()
    )

    return league


def season_quantity(members):
    all_seasons = set(
        rank_models.SeasonScore.objects
        .filter(user__in=members)
        .values_list('season', flat=True)
        .distinct()
    )
    
    return all_seasons


def check_pwd_and_join(league, password, user):
    if league.check_password(password):
        league.members.add(user)
        return True
    else:
        return False
