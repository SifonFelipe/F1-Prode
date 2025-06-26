from predictions.models import Driver, Prediction, RacingTeam, Result, Session, GrandPrix, PredictedPosition, ResultPole, PredictedPole, RaceLineUp
from ranking.models import SeasonScore
from accounts.models import CustomUser

from datetime import datetime, date, timedelta

from F1Prode.static_variables import CURRENT_SEASON

grand_prixs = GrandPrix.objects.filter(date__range=(date(CURRENT_SEASON, 1, 1), date.today() + timedelta(days=1)))
# CHANGE THIS!!!

reset_sessions_to_fwc = True if str(input("Reset sessions to FWC? [Y/n]")).lower() == "y" else False

reset_gp_lu = True if str(input("Delete and reset lineups? [Y/n]")).lower() == "y" else False

if reset_sessions_to_fwc:
    #change state and reset predictions scores
    SeasonScore.objects.filter(season=CURRENT_SEASON).update(points=0)
    CustomUser.objects.all().update(amount_preds=0, amount_preds_correct=0)

    for gp in grand_prixs:
        sessions = Session.objects.filter(grand_prix=gp)
        sessions.update(state="FWC")
        predictions = Prediction.objects.filter(session__in=sessions)
        predictions.update(points_scored=0)
        PredictedPosition.objects.filter(prediction__in=predictions).update(correct=False)
        PredictedPole.objects.filter(prediction__in=predictions).update(correct=False)

reset_all = True if str(input("Reset all? [Y/n]")).lower() == "y" else False

if reset_all:
    grand_prixs.update(ended=False)
    Driver.objects.filter(season=CURRENT_SEASON).update(points=0)
    RacingTeam.objects.filter(season=CURRENT_SEASON).update(points=0)
    SeasonScore.objects.filter(season=CURRENT_SEASON).update(points=0)

    for gp in grand_prixs:
        sessions = Session.objects.filter(grand_prix=gp)
        sessions.update(state="NF")
        Result.objects.filter(session__in=sessions).delete()
        ResultPole.objects.filter(session__in=sessions).delete()

        predictions = Prediction.objects.filter(session__in=sessions)
        predictions.update(points_scored=0)
        PredictedPosition.objects.filter(prediction__in=predictions).update(correct=False)
        PredictedPole.objects.filter(prediction__in=predictions).update(correct=False)

if reset_gp_lu:
    RaceLineUp.objects.filter(session__grand_prix__season__season=CURRENT_SEASON).delete()
    grand_prixs.update(lineup_associated=False)