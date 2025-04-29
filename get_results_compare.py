from predictions.models import GrandPrix, Session, Result, Driver, RacingTeam, Prediction, PredictedPosition, PredictedPole, ResultPole
from accounts.models import CustomUser
from ranking.models import YearScore

from datetime import datetime, timedelta, date

import fastf1

POINTS_BY_POSITION_RACE = {
    1: 5,
    2: 3,
    3: 2,
    4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    11: 0.5, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5,
    16: 0.25, 17: 0.25, 18: 0.25, 19: 0.25, 20: 0.25
}

def update_rankings(year):
    scores = YearScore.objects.filter(year=year).order_by('-points')
    for i, score in enumerate(scores, start=1):
        score.position = i
        score.save()

now = datetime.now()
year = now.year

grand_prixs = GrandPrix.objects.filter(date__range=(date(year, 1, 1), date.today() + timedelta(hours=12)), ended=False)

for gp in grand_prixs:
    print(f"Getting and Comparing data from {gp.name}")

    for session_type in ["Qualifying", "Race"]:
        session = Session.objects.get(grand_prix=gp, session_type=session_type)

        print(f"Fetching {session_type}")
        session_data = fastf1.get_session(year, gp.location, session_type)
        session_data.load()

        fastest_lap = session_data.laps.pick_fastest()
        fastest_driver_n = fastest_lap["DriverNumber"]

        predictions_by_users = Prediction.objects.filter(session=session)
        are_predictions = True if predictions_by_users else False

        if not session_data.results.empty:
            result_dict = {}

            for _, row in session_data.results.iterrows(): #session_data contains the finished positions and more

                driver = Driver.objects.get(number=row["DriverNumber"], last_name=row["LastName"], year=year)
                racing_team = RacingTeam.objects.get(name=row["TeamName"], year=year)

                laps_count = (session_data.laps["DriverNumber"] == row["DriverNumber"]).sum()
                filtered_laps = session_data.laps[(session_data.laps["DriverNumber"] == str(driver.number)) & (session_data.laps["IsPersonalBest"] == True)]

                if not filtered_laps.empty:
                    best_lap_time = filtered_laps.iloc[-1]["LapTime"]
                else:
                    print(f"{driver.last_name} doesnt have a fast lap")
                    best_lap_time = None

                if session_type == "Race":
                    result = Result.objects.create(
                        driver=driver,
                        session=session,
                        position=int(row["Position"]),
                        laps_completed=laps_count,
                        fastest_lap=best_lap_time,
                        fastest_lap_session= True if fastest_driver_n == row["DriverNumber"] else False,
                        disqualified= True if row["ClassifiedPosition"] == "D" else False,
                        for_which_team=racing_team
                    )

                    driver.points += int(row["Points"])
                    driver.save()
                    racing_team.points += int(row["Points"])
                    racing_team.save()

                    result_dict[int(row["Position"])] = driver

                elif session_type == "Qualifying":
                    poleman = driver

                    result = ResultPole.objects.create(
                        driver=driver,
                        session=session,
                        lap_time=best_lap_time,
                        for_which_team=racing_team,
                    )

                    if row["Position"] == "1" or row["Position"] == 1:
                        break

    gp.ended = True
    gp.save()

    for prediction_user in predictions_by_users:
        predictions = PredictedPosition.objects.filter(prediction=prediction_user)

        pole_pred = PredictedPole.objects.filter(prediction=prediction_user)

        total_points = 0

        if pole_pred:
            pole_pred = pole_pred[0]
            
            if poleman == pole_pred.driver:
                total_points = 4

                pole_pred.correct = True
                pole_pred.save()

        guessed = wrong = 0
        prediction_user.points_scored = 0

        for prediction in predictions:
            if result_dict[prediction.position] == prediction.driver:
                total_points += POINTS_BY_POSITION_RACE[prediction.position]
                prediction.correct = True
                prediction.save()

                guessed += 1
            else:
                wrong += 1

        prediction_user.points_scored = total_points
        prediction_user.save()

        user = CustomUser.objects.get(username=prediction_user.user.username)

        user_score, created = YearScore.objects.get_or_create(user=user, year=year)
        user_score.points += total_points
        user_score.save()

update_rankings(year)