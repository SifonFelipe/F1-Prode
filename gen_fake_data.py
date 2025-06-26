import random
from decimal import Decimal
from predictions.models import Prediction, PredictedPosition, PredictedPole
from predictions.models import Session, Driver
from accounts.models import CustomUser as User # o tu modelo custom si tenés uno
from ranking.models import SeasonScore

def create_fake_predictions(num_users=1):
    user = User.objects.get(username="sifon")
    sessions = Session.objects.filter(
        session_type__in=["Race", "Sprint", "Qualifying"]
    ).select_related('grand_prix', 'grand_prix__season')

    drivers = list(Driver.objects.all())
    season_scores = {
        (ss.user_id, ss.season): ss
        for ss in SeasonScore.objects.all()
    }

    predictions_created = 0

    for session in sessions:
        season = session.grand_prix.season

        if Prediction.objects.filter(season_score__user=user, session=session).exists():
            continue  # Evita duplicados por la unique constraint

        # Obtener SeasonScore correspondiente
        season_score = season_scores.get((user.id, season.season))
        if not season_score:
            print(f"No SeasonScore for user {user.username} and season {season}")
            continue

        prediction = Prediction.objects.create(
            session=session,
            season_score=season_score,
            points_scored=Decimal("0.00")
        )

        if session.session_type in ['Race', 'Sprint']:
            random.shuffle(drivers)
            for i, driver in enumerate(drivers[:20], start=1):  # Solo 20 predicciones
                PredictedPosition.objects.create(
                    prediction=prediction,
                    driver=driver,
                    position=i,
                    correct=False  # por defecto
                )

        elif session.session_type == 'Qualifying':
            driver = random.choice(drivers)
            PredictedPole.objects.create(
                prediction=prediction,
                driver=driver,
                correct=False  # por defecto
            )

        predictions_created += 1

    print(f"Se crearon {predictions_created} predicciones.")

# Ejecutar
create_fake_predictions()