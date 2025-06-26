from predictions.models import GrandPrix, Session, Result, Driver, RacingTeam, ResultPole, SeasonSettings
from django.db.models import Prefetch
from datetime import datetime
from django.utils.timezone import make_aware
from F1Prode.static_variables import ALL_SEASONS
import fastf1
import logging


# Disable log for fastf1
logging.getLogger('fastf1').setLevel(logging.CRITICAL)

def get_driver_and_team(row):
    driver = drivers.get(number=row["DriverNumber"], last_name=row["LastName"])
    team = racing_teams.get(name=row["TeamName"])
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


def get_session_and_load(season, gp, session_type):
    print(f"Fetching {session_type} Results... (This may take some time)")

    session_data = fastf1.get_session(season, gp.location, session_type)
    session_data.load()

    return session_data, session_data.results.empty


def process_race_results(session_data, session):
    fastest_lap = session_data.laps.pick_fastest()
    fastest_driver_n = fastest_lap["DriverNumber"]
    result_dict = {}
    results = []
    drivers = []
    teams = []

    for _, row in session_data.results.iterrows():
        driver, team = get_driver_and_team(row)
        laps_count = (session_data.laps["DriverNumber"] == row["DriverNumber"]).sum()
        best_lap_time = get_driver_best_lap(session_data, driver)
        
        results.append(
            Result(
                driver=driver,
                session=session,
                position=int(row["Position"]),
                laps_completed=laps_count,
                fastest_lap=best_lap_time,
                fastest_lap_session= True if fastest_driver_n == row["DriverNumber"] else False,
                disqualified= True if row["ClassifiedPosition"] == "D" else False,
                for_which_team=team
            )
        )

        driver.points += int(row["Points"])
        team.points += int(row["Points"])
        drivers.append(driver)
        teams.append(team)

        result_dict[int(row["Position"])] = driver

    Result.objects.bulk_create(results)
    Driver.objects.bulk_update(drivers, ['points'])
    RacingTeam.objects.bulk_update(teams, ['points'])

    print("Done!")
    # return result_dict  #  If needed


def process_qualifying_results(session_data, session):
    for _, row in session_data.results.iterrows():
        if row["Position"] == 1 or row["Position"] == "1":
            driver, team = get_driver_and_team(row)
            ResultPole.objects.create(
                driver=driver,
                session=session,
                lap_time=row["Q3"],
                for_which_team=team
            )

            break

    print("Done!")


sessions_to_fetch = ["Race", "Sprint", "Qualifying"]
sessions_to_update = []
gps_to_update = []

for season in ALL_SEASONS:
    print(f"Getting results from {season} season")

    # Data to make the query
    from_date = make_aware(datetime(season, 1, 1))
    to_date = make_aware(datetime.now())

    season_settings = (
        SeasonSettings.objects
        .filter(season=season)
        .prefetch_related(
            Prefetch(
                "gps",
                queryset=GrandPrix.objects.filter(
                    ended=False,
                    start_date__range=(from_date, to_date)
                ).prefetch_related(
                    Prefetch(
                        "sessions",
                        queryset=Session.objects.filter(
                            session_type__in=sessions_to_fetch,
                            session_date__range=(from_date, to_date)
                        )
                    )
                )
            ),
            "racing_teams",
            "drivers"
        )
    ).first()

    gps = season_settings.gps.all()
    racing_teams = season_settings.racing_teams.all()
    drivers = season_settings.drivers.all()

    for gp in gps:
        print(f"\nGetting and processing data from {gp.name}")

        if gp.event_format == "sprint_qualifying":
            print("Has Sprint Race!")

        gp_sessions = gp.sessions.all()
        for session in gp_sessions:
            session_type = session.session_type
            session_data, empty = get_session_and_load(season, gp, session_type)

            if not empty:
                print(f"Processing {session_type} Results")

                if session_type == "Race" or session_type == "Sprint":
                    process_race_results(session_data, session)

                elif session_type == "Qualifying":
                    process_qualifying_results(session_data, session)

                session.state = "FWC"  # Finished, Waiting Compare
                sessions_to_update.append(session)

                if session_type == "Race":
                    gp.ended = True
                    gps_to_update.append(gp)

        if empty:
            break

Session.objects.bulk_update(sessions_to_update, ['state'])
GrandPrix.objects.bulk_update(gps_to_update, ['ended'])