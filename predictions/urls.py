from django.urls import path
from . import views


urlpatterns = [
    path('create-pred/<str:season>/<str:location>/<str:session_type>', views.createPred, name="create-pred"),
    path("save_prediction/", views.save_pred, name="save_pred"),
    path("save_champions_pred/<str:season>", views.saveChampionPred, name="save-champion-pred"),
    path("results-comp/<str:user>/<str:season>/<str:location>/<str:session_type>", views.compare_results, name="results-comparision"),
    path("champion-pred/<str:season>", views.championPred, name='champions-pred')
]