import fastf1
import requests

from predictions.models import Driver, RacingTeam, SeasonSettings

season_year = int(input("Enter season to fetch drivers from:\n"))
season = SeasonSettings.objects.get(season=season_year)

f1_data = requests.get('https://api.openf1.org/v1/drivers').json()
for driver_data in f1_data[-100:]: #populate database with drivers info
    new_team, created = RacingTeam.objects.get_or_create(name=driver_data["team_name"], season=season)
    
    driver, _ = Driver.objects.get_or_create(
        season=season,
        first_name = driver_data['first_name'],
        last_name = driver_data['last_name'],
        number = driver_data['driver_number'],
        racing_team = new_team,
        country = driver_data['country_code'],
        headshot = driver_data['headshot_url']
    )

    new_team.save()
    driver.save()