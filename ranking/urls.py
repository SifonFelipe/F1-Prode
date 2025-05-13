from django.urls import path, re_path
from . import views


urlpatterns = [
    re_path(r'^(?P<year>\d{4})/$', views.global_ranking, name="ranking"), #regular expression to not collide with create-league
    path('create-league', views.createLeague, name='create-league'),
    path('league/<str:username>/<str:leaguename>', views.viewLeague, name='view-league'),
    path('<str:username>/<str:leaguename>/join', views.join_league, name='join-league'),
    path('<str:username>/<str:leaguename>/leave', views.leave_league, name='leave-league'),
]