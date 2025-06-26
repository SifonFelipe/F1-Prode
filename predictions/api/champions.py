from predictions import models as pm
from datetime import datetime, timezone
from django.db.models import Prefetch


def get_teams_and_drivers(season, countdown_ch=False):
    s_settings = (
        pm.SeasonSettings.objects
        .filter(season=season)
        .prefetch_related(
            Prefetch(
                "racing_teams",
                to_attr='teams'
            ),
            Prefetch(
                "drivers",
                to_attr='driversset'
            )
        )
    ).first()

    teams = s_settings.teams
    drivers = s_settings.driversset

    if countdown_ch:
        countdown = s_settings.limit_ch_pred.isoformat()
        return teams, drivers, countdown

    return teams, drivers


def save_champions(request, user, season):
    driver = request['driver_champion']
    team = request['team_champion']

    settings = (
        pm.SeasonSettings.objects
        .filter(season=season)
        .prefetch_related(
            Prefetch(
                "drivers",
                queryset=pm.Driver.objects.filter(id=driver),
                to_attr="driver"
            ),
            Prefetch(
                "racing_teams",
                queryset=pm.RacingTeam.objects.filter(id=team),
                to_attr="team"
            )
        )
    ).first()

    if settings.limit_ch_pred < datetime.now(timezone.utc).date():
        return False
    
    pm.ChampionPrediction.objects.update_or_create(
        season_score__user=user,
        defaults={'driver': settings.driver[0], 'team': settings.team[0]}
    )

    return True
