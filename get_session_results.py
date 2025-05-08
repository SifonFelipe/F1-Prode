from predictions.models import GrandPrix, Session, Result, Driver, RacingTeam, ResultPole

from datetime import datetime, timedelta, date

import fastf1
import logging

#disable log for fastf1
logging.getLogger('fastf1').setLevel(logging.CRITICAL)

def get_driver_and_team(row, year):
    driver = Driver.objects.get(number=row["DriverNumber"], last_name=row["LastName"], year=year)
    team = RacingTeam.objects.get(name=row["TeamName"], year=year)
    return driver, team

def get_driver_best_lap(session_data, driver):
    filtered_laps = session_data.laps[
        (session_data.laps["DriverNumber"] == str(driver.number)) & 
        (session_data.laps["IsPersonalBest"] == True)
    ]

    if not filtered_laps.empty:
        return filtered_laps.iloc[-1]["LapTime"]
    print(f"{driver.last_name} didn't complete a lap!")
    return None

def get_session_and_load(gp, session_type, year):
    print(f"Fetching {session_type} Results... (This may take some time)")

    session = Session.objects.get(grand_prix=gp, session_type=session_type)
    session_data = fastf1.get_session(year, gp.location, session_type)
    session_data.load()

    print("Done!\n")

    return session, session_data

def process_race_results(session_data, session, year):
    print(f"Processing Race Results...")

    fastest_lap = session_data.laps.pick_fastest()
    fastest_driver_n = fastest_lap["DriverNumber"]
    result_dict = {}

    for _, row in session_data.results.iterrows():
        driver, team = get_driver_and_team(row, year)
        laps_count = (session_data.laps["DriverNumber"] == row["DriverNumber"]).sum()
        best_lap_time = get_driver_best_lap(session_data, driver)
        
        result = Result.objects.create(
            driver=driver,
            session=session,
            position=int(row["Position"]),
            laps_completed=laps_count,
            fastest_lap=best_lap_time,
            fastest_lap_session= True if fastest_driver_n == row["DriverNumber"] else False,
            disqualified= True if row["ClassifiedPosition"] == "D" else False,
            for_which_team=team
        )

        driver.points += int(row["Points"])
        driver.save()
        team.points += int(row["Points"])
        team.save()
        result_dict[int(row["Position"])] = driver

    print("Done!\n")
    return result_dict

def process_qualifying_results(session_data, session, year):
    print(f"Processing Qualifying Results...")

    for _, row in session_data.results.iterrows():
        if row["Position"] == 1 or row["Position"] == "1":
            driver, team = get_driver_and_team(row, year)
            ResultPole.objects.create(
                driver=driver,
                session=session,
                lap_time=row["Q3"],
                for_which_team=team
            )

            break

    print("Done!\n")
    
now = datetime.now()
year = now.year

grand_prixs = GrandPrix.objects.filter(date__range=(date(year, 1, 1), date.today() + timedelta(hours=12)), ended=False)

for gp in grand_prixs:
    print(f"\nGetting and Comparing data from {gp.name}")

    for session_type in ["Qualifying", "Race"]:
        session, session_data = get_session_and_load(gp, session_type, year)

        if not session_data.results.empty:
            if session_type == "Race":
                result_dict = process_race_results(session_data, session, year)

            elif session_type == "Qualifying":
                process_qualifying_results(session_data, session, year)

            session.state = "FWC" #Finished, Waiting Compare
            session.save()

    gp.ended = True
    gp.save()