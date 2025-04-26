from django.urls import path
from . import views


urlpatterns = [
    path('<str:year>', views.global_ranking, name="ranking"),
]