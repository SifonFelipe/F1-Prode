from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q, Prefetch
from django.contrib import messages

from .models import YearScore, PrivateLeague
from predictions.models import GrandPrix
from accounts.models import CustomUser
from .forms import PrivateLeagueForm

from F1Prode.static_variables import CURRENT_SEASON

from itertools import chain 

def global_ranking(request, season):
    filter_mode = request.GET.get('filter', 'all')
    user = request.user

    if filter_mode == 'friends' and user.is_authenticated:
        friend_ids = user.friends.values_list('id', flat=True) #friends ids

        scores_qs = YearScore.objects.filter(user__in=friend_ids, season=season).select_related('user') #scores and user data

        my_score = YearScore.objects.filter(user=user, season=season).select_related('user').first()

        if my_score and my_score.user_id not in friend_ids:
            scores = list(chain([my_score], scores_qs))
        else:
            scores = list(scores_qs)

        scores = sorted(scores, key=lambda x: x.points, reverse=True) #order_by but in a list
        user_score = my_score
    else:
        scores_qs = YearScore.objects.filter(season=season).select_related('user').order_by('-points') #all the results
        scores = list(scores_qs)

        user_score = next((s for s in scores if s.user_id == user.id), None)

    paginator = Paginator(scores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # in a single query get finished and not finished gps
    races_counts = (
        GrandPrix.objects
        .filter(season=season)
        .aggregate(
            total_races=Count('id'),
            races_completed=Count('id', filter=Q(ended=True))
        )
    )

    context = {
        "scores": scores,
        "season": season,
        "races_completed": races_counts['races_completed'],
        "total_races": races_counts['total_races'],
        "amount_users": len(scores),
        "page_obj": page_obj,
        "user_score": user_score,
        "filter": filter_mode,
    }

    return render(request, "ranking.html", context)

def createLeague(request):
    print(request.user)

    if request.method == "POST":
        form = PrivateLeagueForm(request.POST)

        if form.is_valid():
            form.save(creator=request.user)
            return redirect('home')
        
    else:
        form = PrivateLeagueForm()

    return render(request, 'create_league.html', {'form': form})

def viewLeague(request, username, leaguename):
    creator = (
        CustomUser.objects
        .filter(username=username)
        .prefetch_related(
            Prefetch(
                "created_leagues",
                queryset=PrivateLeague.objects.filter(name=leaguename).prefetch_related("members__season_scores")
            ),
        )
    ).first()

    league = creator.created_leagues.all().first()
    members = league.members.all()

    all_seasons = set()
    for member in members:
        for score in member.season_scores.all():
            all_seasons.add(score.season)

    seasons = sorted(all_seasons, reverse=True)

    context = {'league': league, 'members': members, 'seasons': seasons}
    return render(request, "view_league.html", context)


def join_league(request, username, leaguename):
    if request.method == "POST":
        password = request.POST.get("password", "")
        user = request.user

        creator=(
            CustomUser.objects
            .filter(username=username)
            .prefetch_related(
                Prefetch(
                    "created_leagues",
                    queryset=PrivateLeague.objects.filter(name=leaguename).prefetch_related("members")
                )
            )
        ).first()

        league = creator.created_leagues.all().first()

        if league.check_password(password):
            league.members.add(user)
            messages.success(request, "You joined successfully.")
        else:
            messages.error(request, "Incorrect password.")

    return redirect("view-league", username=username, leaguename=leaguename)

def leave_league(request, username, leaguename):
    if request.method == "POST":
        user = request.user
        creator=(
            CustomUser.objects
            .filter(username=username)
            .prefetch_related(
                Prefetch(
                    "created_leagues",
                    queryset=PrivateLeague.objects.filter(name=leaguename)
                )
            )
        ).first()

        league = creator.created_leagues.all().first()
        league.members.remove(user)

    return redirect("view-league", username=username, leaguename=leaguename)