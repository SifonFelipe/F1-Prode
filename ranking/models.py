from django.db import models
from F1Prode.static_variables import CURRENT_SEASON
from django.conf import settings

class SeasonScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="season_scores")
    season = models.IntegerField(default=CURRENT_SEASON)
    points = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    position = models.IntegerField(default=0)
    gps_participated = models.IntegerField(default=0)

    class Meta:
        ordering = ['-points', 'user__username']

    def __str__(self):
        return f"[{self.season}] {self.user}"
