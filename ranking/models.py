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

class PrivateLeague(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_leagues')
    members = models.ManyToManyField(CustomUser, related_name="leagues")
    password = models.CharField(max_length=128) # hasheada

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['creator', 'name'], name='unique_league_name_per_creator')
        ]

    def check_password(self, raw_password):
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)
        self.save()

    def __str__(self):
        return f"[{self.creator.username}] {self.name}"

class Invitation(models.Model):
    from_who = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="invitations_sent")
    to_who = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="invitations_received")
    to_league = models.ForeignKey(PrivateLeague, on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.to_league}] {self.from_who} to {self.to_who}"