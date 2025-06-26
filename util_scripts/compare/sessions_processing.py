from predictions.api import get_points_system
from .comparators import compare_session_preds
from .helpers import list_season_scores, transform_user_dict_to_list, race_results_list
from ranking.models import SeasonScore

SESSION_CONFIG = {
    "Race": {"result_func": race_results_list},
    "Sprint": {"result_func": race_results_list},
    "Qualifying": {"result_func": lambda session: session.pole[0]},
}

def process_sessions(sessions_to_compare):
    last_setting = None
    season_scores = {}
    users_stats = {}
    seasons_compared = []

    update_session_status = []
    update_season_scores = []
    update_prediction = []
    update_poles_predictions = []
    update_positions_predictions = []

    for session in sessions_to_compare:
        session_type = session.session_type
        season = session.grand_prix.season

        print(f"Comparing Results with Predictions of {session_type} - {session.grand_prix.name}")

        if last_setting != season:
            last_setting = season
            scoring = get_points_system(season, None, return_complete=True)

            if season_scores:
                update_season_scores.extend(list_season_scores(season_scores))

            season_scores = {
                s: 0 for s in SeasonScore.objects.filter(season=season.season)
            }
            seasons_compared.append(season)

        score_format = scoring[session_type]
        result = SESSION_CONFIG[session_type]["result_func"](session)

        preds, pos_preds, season_scores, users_stats = compare_session_preds(
            session=session,
            results=result,
            score_format=score_format,
            s_scores=season_scores,
            users_stats=users_stats,
        )

        update_prediction.extend(preds)

        if session_type in ["Race", "Sprint"]:
            update_positions_predictions.extend(pos_preds)
        elif session_type == "Qualifying":
            update_poles_predictions.extend(pos_preds)

        session.state = "F"
        update_session_status.append(session)

        print("Done!\n")

    update_season_scores.extend(list_season_scores(season_scores))
    update_user_stats = transform_user_dict_to_list(users_stats)

    return {
        "update_session_status": update_session_status,
        "update_prediction": update_prediction,
        "update_poles_predictions": update_poles_predictions,
        "update_positions_predictions": update_positions_predictions,
        "update_season_scores": update_season_scores,
        "update_user_stats": update_user_stats,
        "seasons_compared": seasons_compared,
    }
