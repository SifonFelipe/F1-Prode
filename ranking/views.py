from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count, Q

from .models import YearScore
from predictions.models import GrandPrix

from datetime import datetime
from itertools import chain

year = datetime.now().year 

def global_ranking(request, year):
    year = int(year)
    filter_mode = request.GET.get('filter', 'all')
    user = request.user

    if filter_mode == 'friends' and user.is_authenticated:
        friend_ids = user.friends.values_list('id', flat=True) #friends ids

        scores_qs = YearScore.objects.filter(user__in=friend_ids, year=year).select_related('user') #scores and user data

        my_score = YearScore.objects.filter(user=user, year=year).select_related('user').first()

        if my_score and my_score.user_id not in friend_ids:
            scores = list(chain([my_score], scores_qs))
        else:
            scores = list(scores_qs)

        scores = sorted(scores, key=lambda x: x.points, reverse=True) #order_by but in a list
        user_score = my_score
    else:
        scores_qs = YearScore.objects.filter(year=year).select_related('user').order_by('-points') #all the results
        scores = list(scores_qs)

        user_score = next((s for s in scores if s.user_id == user.id), None)

    paginator = Paginator(scores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # in a single query get finished and not finished gps
    races_counts = (
        GrandPrix.objects
        .filter(year=year)
        .aggregate(
            total_races=Count('id'),
            races_completed=Count('id', filter=Q(ended=True))
        )
    )

    context = {
        "scores": scores,
        "year": year,
        "races_completed": races_counts['races_completed'],
        "total_races": races_counts['total_races'],
        "amount_users": len(scores),
        "page_obj": page_obj,
        "user_score": user_score,
        "filter": filter_mode,
    }

    return render(request, "ranking.html", context)