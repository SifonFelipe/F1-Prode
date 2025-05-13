from django.contrib import admin
from .models import PrivateLeague, YearScore, Invitation
# Register your models here.
admin.site.register([PrivateLeague, Invitation])