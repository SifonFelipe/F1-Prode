from django.shortcuts import render
from django.core.paginator import Paginator

from .models import YearScore
from predictions.models import GrandPrix
from ranking.models import CustomUser

from datetime import datetime
from itertools import chain

year = datetime.now().year 

def global_ranking(request, year):
    year = int(year)
    filter_mode = request.GET.get('filter', 'all')
    user = request.user

    if filter_mode == 'friends' and user.is_authenticated:
        friend_ids = user.friends.values_list('id', flat=True)
        scores_qs = YearScore.objects.filter(user__in=friend_ids, year=year).select_related('user')
        my_score = YearScore.objects.filter(user=user, year=year).first()

        if my_score and my_score.user_id not in friend_ids:
            scores = list(chain([my_score], scores_qs))
        else:
            scores = list(scores_qs)

        scores = sorted(scores, key=lambda x: x.points, reverse=True)
        user_score = my_score
    else:
        scores = YearScore.objects.filter(year=year).order_by('-points').select_related('user')
        user_score = YearScore.objects.filter(user=user, year=year).first()

    paginator = Paginator(scores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    races_completed = GrandPrix.objects.filter(year=year, ended=True).count()
    total_races = GrandPrix.objects.filter(year=year).count()

    context = {
        "scores": scores,
        "year": year,
        "races_completed": races_completed,
        "total_races": total_races,
        "amount_users": len(scores),
        "page_obj": page_obj,
        "user_score": user_score,
        "filter": filter_mode,
    }

    return render(request, "ranking.html", context)