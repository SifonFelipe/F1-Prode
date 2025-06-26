from predictions import models as pm
from ranking.models import SeasonScore

def update_rankings_and_participations(seasons):
    """
    Update SeasonScore.position property (1, 2, 3, etc)
    If a user participated on a gp, it count as one (SeasonScore.gps_participated)
    """

    for season in seasons:
        season_scores_for_season = list(
            SeasonScore.objects.filter(
                season=season.season
            ).order_by('-points')
        )

        for idx, season_score in enumerate(season_scores_for_season):
            season_score.position = idx + 1

        participation_map = {}
        for season_score in season_scores_for_season:
            unique_gps = set(
                pm.Prediction.objects
                .filter(season_score=season_score, session__grand_prix__season=season,
                        session__grand_prix__ended=True)
                .values_list('session__grand_prix_id', flat=True)
            )

            participation_map[season_score.id] = len(unique_gps)

        for season_score in season_scores_for_season:
            season_score.gps_participated = participation_map.get(season_score.id, 0)

        SeasonScore.objects.bulk_update(season_scores_for_season, ['position', 'gps_participated'])
