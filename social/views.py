from django.shortcuts import render
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q, Prefetch
from django.contrib import messages

from social.models import PrivateLeague
from ranking import models as rank_models
from accounts.models import CustomUser
from .forms import PrivateLeagueForm
from predictions import api as prediction_api
from ranking import api as ranking_api

def createLeague(request):
    if request.method == "POST":
        form = PrivateLeagueForm(request.POST)

        if form.is_valid():
            form.save(creator=request.user)
            return redirect('home')
        
    else:
        form = PrivateLeagueForm()

    return render(request, 'create_league.html', {'form': form})

def get_league(username, leaguename):
    league = (
        PrivateLeague.objects
        .filter(name=leaguename, creator__username=username)
        .prefetch_related("members__season_scores")
        .first()
    )

    return league


def season_quantity(members):
    all_seasons = set(
        rank_models.SeasonScore.objects
        .filter(user__in=members)
        .values_list('season', flat=True)
        .distinct()
    )
    
    return all_seasons


def viewLeague(request, username, leaguename):
    league = get_league(username, leaguename)
    members = league.members.all()
    all_seasons = season_quantity(members)

    seasons = sorted(all_seasons, reverse=True)

    context = {'league': league, 'members': members, 'seasons': seasons}
    return render(request, "view_league.html", context)


def check_pwd_and_join(league, password, user):
    if league.check_password(password):
        league.members.add(user)
        return True
    else:
        return False


def join_league(request, username, leaguename):
    if request.method == "POST":
        password = request.POST.get("password", "")
        user = request.user

        league = get_league(username, leaguename)

        success = check_pwd_and_join(league, password, user)

        if success:
            messages.success(request, "You joined successfully.")
        else:
            messages.error(request, "Incorrect password.")

    return redirect("view-league", username=username, leaguename=leaguename)

def leave_league(request, username, leaguename):
    if request.method == "POST":
        user = request.user
        league = get_league(username, leaguename)
        league.members.remove(user)

    return redirect("view-league", username=username, leaguename=leaguename)