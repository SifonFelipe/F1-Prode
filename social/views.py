from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PrivateLeagueForm
from social import api as social_api

def createLeague(request):
    if request.method == "POST":
        form = PrivateLeagueForm(request.POST)

        if form.is_valid():
            form.save(creator=request.user)
            return redirect('home')
        
    else:
        form = PrivateLeagueForm()

    return render(request, 'create_league.html', {'form': form})


def viewLeague(request, username, leaguename):
    league = social_api.get_league(username, leaguename)
    members = league.members.all()
    all_seasons = social_api.season_quantity(members)

    seasons = sorted(all_seasons, reverse=True)

    context = {'league': league, 'members': members, 'seasons': seasons}
    return render(request, "view_league.html", context)


def join_league(request, username, leaguename):
    if request.method == "POST":
        password = request.POST.get("password", "")
        user = request.user

        league = social_api.get_league(username, leaguename)

        success = social_api.check_pwd_and_join(league, password, user)

        if success:
            messages.success(request, "You joined successfully.")
        else:
            messages.error(request, "Incorrect password.")

    return redirect("view-league", username=username, leaguename=leaguename)

def leave_league(request, username, leaguename):
    if request.method == "POST":
        user = request.user
        league = social_api.get_league(username, leaguename)
        league.members.remove(user)

    return redirect("view-league", username=username, leaguename=leaguename)