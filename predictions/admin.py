from django.contrib import admin
from predictions import models as pm

admin.site.register(
    [
        pm.Driver, pm.GrandPrix, pm.Session, pm.RacingTeam, pm.Result,
        pm.Prediction, pm.PredictedPosition, pm.PredictedPole, pm.ResultPole,
        pm.ChampionPrediction, pm.SeasonSettings, pm.RaceLineUp
    ]
)
