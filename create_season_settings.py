from predictions.models import SeasonSettings
import json

season = int(input("Enter season year:\n"))

amount_drivers = int(input("\nEnter amount of drivers:\n"))

qualy_points_pred = int(input("\nEnter amount of points from POLE prediction:\n"))

race_points_pred = {}
sprint_points_pred = {}

for idx, point_pred in enumerate([race_points_pred, sprint_points_pred]):
    if idx == 0:
        print("\nFillings points dict for race predictions")
    else:
        print("\nFillings points dict for sprint race predictions")

    x = 1
    while x < 21:
        if x == 4:
            points = float(input("\nEnter points from 4 to 10 position:\n"))
            for y in range(x, 11):
                point_pred[y] = points

            x = 11

        elif x == 11 or x == 16:
            points = float(input(f"\nEnter points from {x} to {x+4} position:\n"))
            for y in range(x, x+4):
                point_pred[y] = points

            x += 5

        else:
            points = float(input(f"\nEnter points for {x} position:\n"))
            point_pred[x] = points

            x += 1

SeasonSettings.objects.update_or_create(
    season=season,
    defaults={
        'amount_drivers': amount_drivers,
        'amount_teams': amount_drivers / 2,
        'race_points_pred': json.dumps(race_points_pred),
        'sprint_points_pred': json.dumps(sprint_points_pred),
        'qualy_points_pred': qualy_points_pred,
    }
)
