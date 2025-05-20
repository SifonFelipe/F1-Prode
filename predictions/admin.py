from django.contrib import admin
from .models import Driver, GrandPrix, Session, RacingTeam, Result, Prediction, PredictedPosition, PredictedPole, ResultPole, ChampionPrediction

admin.site.register([Driver, GrandPrix, Session, RacingTeam, Result, Prediction, PredictedPosition, PredictedPole, ResultPole, ChampionPrediction])
