from django.shortcuts import render
from django.core.paginator import Paginator
from predictions import api as prediction_api
from ranking import api as ranking_api

def create_paginator_and_page(list, amount_by_page, page_number):
    paginator = Paginator(list, amount_by_page)
    page_obj = paginator.get_page(page_number)

    return page_obj


def global_ranking(request, season):
    filter_mode = request.GET.get('filter', 'all')
    user = request.user

    if filter_mode == 'friends' and user.is_authenticated:
        friends_score = list(
            ranking_api.get_user_and_friends_with_score(
                user=user,
                season=season
            )
        )

        # order_by but in a list
        scores = sorted(friends_score, key=lambda x: x.points, reverse=True)

    else:
        scores = ranking_api.get_season_scores(season)

    user_score = next((s for s in scores if s.user_id == user.id), None)

    page_number = request.GET.get('page')
    page_obj = create_paginator_and_page(scores, 10, page_number)

    total_gps, ended_gps = prediction_api.season_gps_status(season)

    context = {
        "scores": scores,
        "season": season,
        "races_completed": ended_gps,
        "total_races": total_gps,
        "amount_users": len(scores),
        "page_obj": page_obj,
        "user_score": user_score,
        "filter": filter_mode,
    }

    return render(request, "ranking.html", context)
