from django.db import models

from accounts.models import CustomUser
from predictions.models import Prediction

from datetime import datetime

year = datetime.now().year

class YearScore(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    year = models.IntegerField(default=year)
    points = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    position = models.IntegerField(default=0)

    def amount_predictions(self):
        return Prediction.objects.filter(user=self.user, session__grand_prix__year=self.year).count()

    class Meta:
        ordering = ['-points', 'user__username']

    def __str__(self):
        return f"{self.user.username} - {year}"