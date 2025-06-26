from django.urls import re_path
from . import views

urlpatterns = [

    # regular expression to not collide with create-league
    re_path(r'^(?P<year>\d{4})/$', views.global_ranking, name="ranking"),
]