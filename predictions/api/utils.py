from predictions import models as pm
from django.db.models import Q, Count


def season_gps_status(season):
    gp_count = (
        pm.GrandPrix.objects
        .filter(season__season=season)
        .aggregate(
            total_gps=Count('id'),
            gps_ended=Count('id', filter=Q(ended=True))
        )
    )

    return gp_count['total_gps'], gp_count['gps_ended']
