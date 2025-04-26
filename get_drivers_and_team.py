import fastf1
import requests

from predictions.models import Driver, RacingTeam

f1_data = requests.get('https://api.openf1.org/v1/drivers').json()
for driver_data in f1_data[-20:]: #populate database with drivers info
    driver, _ = Driver.objects.get_or_create(
        first_name = driver_data['first_name'],
        last_name = driver_data['last_name'],
        number = driver_data['driver_number'],
        team_name = driver_data['team_name'],
        country = driver_data['country_code'],
        headshot = driver_data['headshot_url']
    )

    new_team, created = RacingTeam.objects.get_or_create(name=driver_data["team_name"])
    
    if created:
        new_team.driver1 = driver
    else:
        if new_team.driver1 == None:
            new_team.driver1 = driver
        elif new_team.driver2 == None:
            new_team.driver2 = driver

    new_team.save()