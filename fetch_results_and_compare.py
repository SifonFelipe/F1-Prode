import fastf1
import datetime

from datetime import date, timedelta

from predictions.models import GrandPrix, Session, Result, Driver, RacingTeam, Prediction, PredictedPosition
from accounts.models import CustomUser
from ranking.models import YearScore

def update_rankings(year):
    scores = YearScore.objects.filter(year=year).order_by('-points')
    for i, score in enumerate(scores, start=1):
        score.position = i
        score.save()

now = datetime.datetime.today()
year = now.year

#getting the gps with the date range (+1day just in case the information is not available)
grand_prixs = GrandPrix.objects.filter(date__range=(date(year, 1, 1), date.today() + timedelta(days=1)), ended=False)

POINTS_BY_POSITION_RACE = {
    1: 5,
    2: 3,
    3: 2,
    4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    11: 0.5, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5,
    16: 0.25, 17: 0.25, 18: 0.25, 19: 0.25, 20: 0.25
}

for idx, gp in enumerate(grand_prixs):

    print(f"Fetching {gp.name}")
    result_dict = {}    #for comparing later

    race = Session.objects.get(grand_prix=gp, session_type="Race")
    race_data = fastf1.get_session(year, idx+1, "Race") #getting session by round number
    race_data.load()

    fastest_lap = race_data.laps.pick_fastest()
    fastest_driver_n = fastest_lap["DriverNumber"]

    try:
        #if overlapping results
        Result.objects.filter(session=race).delete()
    except:
        None

    try:
        #get predictions made by users
        predictions_by_users = Prediction.objects.filter(session=race)
        are_predictions = True
    except:
        are_predictions = False

    if not race_data.results.empty:

        for _, row in race_data.results.iterrows(): #race_data.results contains the finished positions and more

            driver = Driver.objects.get(number=row["DriverNumber"], last_name=row["LastName"])
            racing_team = RacingTeam.objects.get(name=row["TeamName"], year=year)
            laps_count = (race_data.laps["DriverNumber"] == row["DriverNumber"]).sum()

            filtered_laps = race_data.laps[(race_data.laps["DriverNumber"] == str(driver.number)) & (race_data.laps["IsPersonalBest"] == True)]

            if not filtered_laps.empty:
                best_lap_time = filtered_laps.iloc[-1]["LapTime"]
            else:
                print(f"{driver.last_name} doesnt have a fast lap")
                best_lap_time = None

            result = Result.objects.create(
                driver=driver,
                session=race,
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

        gp.ended = True     #update the state of the gp
        gp.save()

        for predictions_user in predictions_by_users:
            predictions = PredictedPosition.objects.filter(prediction=predictions_user)
            total_points = 0
            predictions_user.points_scored = 0
            guessed = 0
            wrong = 0

            for prediction in predictions:
                if result_dict[prediction.position] == prediction.driver:
                    total_points += POINTS_BY_POSITION_RACE[prediction.position]
                    prediction.correct = True
                    prediction.save()
                    guessed += 1
                else:
                    wrong += 1

            predictions_user.points_scored = float(predictions_user.points_scored) + total_points
            predictions_user.save()

            user = CustomUser.objects.get(username=predictions_user.user.username)

            user_score, created = YearScore.objects.get_or_create(user=user, year=year)
            user_score.points += total_points
            user_score.save()

update_rankings(2025)