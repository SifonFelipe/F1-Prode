from predictions.models import Driver, Prediction, RacingTeam, Result, Session, GrandPrix, PredictedPosition
from ranking.models import YearScore

from datetime import datetime, date, timedelta

year = datetime.today().year

grand_prixs = GrandPrix.objects.filter(date__range=(date(year, 1, 1), date.today() + timedelta(days=1)))
grand_prixs.update(ended=False)

Driver.objects.filter(year=year).update(points=0)
RacingTeam.objects.filter(year=year).update(points=0)
YearScore.objects.filter(year=year).update(points=0)

for gp in grand_prixs:
    sessions = Session.objects.filter(grand_prix=gp)

    for session in sessions:
        Result.objects.filter(session=session).delete()

        predictions = Prediction.objects.filter(session=session)
        predictions.update(points_scored=0)

        PredictedPosition.objects.filter(prediction__in=predictions).update(correct=False)