from predictions.models import GrandPrix
from datetime import timedelta

gps = GrandPrix.objects.all()
print(gps)
for gp in gps:
    date = gp.date
    gp.start_date = date - timedelta(days=2)
    print(date, gp.start_date)
    gp.save()

gps = GrandPrix.objects.all()

for gp in gps:
    print(gp.start_date)