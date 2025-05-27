from predictions.models import RaceLineUp, Driver, RacingTeam, Session, GrandPrix
from fastf1 import get_session
from datetime import datetime
from django.utils.timezone import make_aware
from django.db.models import Prefetch
from F1Prode.static_variables import ALL_SEASONS
import logging

#  Disabling log
logging.getLogger('fastf1').setLevel(logging.CRITICAL)

def fetch_teams_drivers_db(season):
    teams = (
        RacingTeam.objects
        .filter(season__season=season)
        .prefetch_related(
            Prefetch(
                "drivers",
                queryset=Driver.objects.filter(is_active=True)
            )
        )
    )

    lu_dict = {}
    for team in teams:
        drivers = set()
        for driver in team.drivers.all():
            drivers.add(driver)

        lu_dict[team] = drivers
    
    return lu_dict


def list_to_int(d_set):
    new_set = set()

    for x in d_set:
        new_set.add(int(x))

    return new_set


def create_lineups(drivers, lu_models, race):
    for driver in drivers:
        lu_models.append(
            RaceLineUp(
                driver=driver,
                team=driver.racing_team,
                session=race,
            )
        )

    return lu_models


lu_objects = []
gp_objects = []

for season in ALL_SEASONS:
    from_date = make_aware(datetime(season, 1, 1))
    to_date = make_aware(datetime.now())

    gps = (
        GrandPrix.objects
        .filter(
            start_date__range=(from_date, to_date),
            lineup_associated=False,
        )
        .select_related('season')
        .prefetch_related(
            Prefetch(
                "sessions",
                queryset=Session.objects.filter(
                    session_type__in=["Practice 1", "Practice 2", "Race"]
                )
            )
        )
    )

    drivers_db = (
        Driver.objects
        .filter(season__season=season)
        .select_related('racing_team')
    )

    if gps:
        for gp in gps:
            print(f"Creating LineUp for {gp.name}\nFetching official drivers")

            if gp.event_format == "conventional":
                session = get_session(gp.season.season, gp.location, 'Practice 2')
            else:
                session = get_session(gp.season.season, gp.location, 'Practice 1')

            session.load()
            print("Done!")

            if session:
                print("Creating LineUp object")
                lu_drivers = set(session.drivers)  # lu = lineup
                lu_drivers = list_to_int(lu_drivers)

                lu_drivers = drivers_db.filter(number__in=lu_drivers)

                race_obj = gp.sessions.all().get(session_type="Race")

                lu_objects = create_lineups(lu_drivers, lu_objects, race_obj)

                gp.lineup_associated = True
                gp_objects.append(gp)

                print("Done!\n")
            else:
                print(f"Couldn't fetch any session of {gp.name}\n")

    GrandPrix.objects.bulk_update(gp_objects, ['lineup_associated'])
    gp_objects = []

    future_gps = (
        GrandPrix.objects
        .filter(
            season__season=season,
            lineup_associated=False,
        )
        .prefetch_related(
            Prefetch(
                "sessions",
                queryset=Session.objects.filter(session_type="Race").prefetch_related(
                    "drivers"
                ),
                to_attr="race"
            )
        )
    )

    if future_gps:
        print("Adding default lineups for remaining sessions")

        default_lu_dict = fetch_teams_drivers_db(season)
        for gp in future_gps:
            race = gp.race[0]

            if not race.drivers.all():
                print(f"Creating default lineup for {gp.name}")

                for team, drivers in default_lu_dict.items():
                    for driver in drivers:
                        lu_objects.append(
                            RaceLineUp(
                                driver=driver,
                                team=driver.racing_team,
                                session=race
                            )
                        )

                print("Done!\n")
            else:
                print(f"{gp.name} has already a default lineup\n")

RaceLineUp.objects.bulk_create(lu_objects)