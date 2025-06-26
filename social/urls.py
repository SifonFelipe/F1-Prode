from django.urls import path
from . import views

urlpatterns = [  
    path('create-league', views.createLeague, name='create-league'),
    path('league/<str:username>/<str:leaguename>', views.viewLeague, name='view-league'),
    path('<str:username>/<str:leaguename>/join', views.join_league, name='join-league'),
    path('<str:username>/<str:leaguename>/leave', views.leave_league, name='leave-league'),
]