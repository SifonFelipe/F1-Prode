import fastf1
import logging
from datetime import timedelta
from predictions.models import GrandPrix, Session, SeasonSettings

# disable logs for fastf1
logging.getLogger('fastf1').setLevel(logging.CRITICAL)

# run this within a year
season = int(input("Enter season you want to download"))

schedule = fastf1.get_event_schedule(season)  # schedule with all the gp's information

# depending on the format of the gp
conventional = ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]
sprint_qualifying = ["Practice 1", "Sprint Qualifying", "Sprint", "Qualifying", "Race"]

season = SeasonSettings.objects.get(season=season)

for _, row in schedule.iterrows():
    if row["Session5"] == "Race":  # evades the testings gps
        gp, created = GrandPrix.objects.get_or_create(
            name=row['EventName'],
            defaults={
                "location": row['Location'],
                "country": row["Country"],
                "date": row["EventDate"],
                "start_date": row["EventDate"] - timedelta(days=2),
                "n_round": row["RoundNumber"],
                "event_format": row["EventFormat"],
                "season": season,
            }
        )

        if created:
            if gp.event_format == "conventional":
                sessions_format = conventional.copy()
            else:
                sessions_format = sprint_qualifying.copy()

            for idx, session in enumerate(sessions_format):
                ses = Session.objects.get_or_create(
                    session_date=row[f"Session{idx+1}DateUtc"],  # "Session{idx}DateUtc" contains the start time of every session
                    grand_prix=gp,
                    session_type=session,
                )

            print(f"{gp.name} added.")
        else:
            print(f"{gp.name} already existed on db.")
