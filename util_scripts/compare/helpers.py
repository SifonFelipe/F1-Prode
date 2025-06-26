from decimal import Decimal

def race_results_list(session):
    """
    Creates a list with the results of the session, in order.
    """
    return [
        result.driver.number
        for result in session.results
    ]


def list_season_scores(s_scores):
    s_scores_objs = []

    for s_score, points in s_scores.items():
        s_score.points = Decimal(str(points))
        s_scores_objs.append(s_score)

    return s_scores_objs


def transform_user_dict_to_list(users_stats):
    users_to_update = []

    for user, guesses in users_stats.items():
        user.amount_preds += guesses["guesses"]
        user.amount_preds_correct += guesses["correct"]
        user.best_prediction = guesses["best_pred"]

        users_to_update.append(user)

    del users_stats
    return users_to_update
