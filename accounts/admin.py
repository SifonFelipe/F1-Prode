from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FriendRequest
from ranking.models import YearScore

from datetime import datetime

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff']
    #fieldsets = UserAdmin.fieldsets + (('Custom Fields', {'fields': ('points',)}),)

    def get_points(self, obj):
        current_year = datetime.now().year
        score = YearScore.objects.filter(user=obj, year=current_year).first()
        return score.points if score else 0

    get_points.short_description = 'Points'  # nombre de la columna en el admin

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register([YearScore, FriendRequest])
