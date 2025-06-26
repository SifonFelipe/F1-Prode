from decimal import Decimal

def compare_qualifying(result, pred, score_format):
    pole_pred = pred.predicted_pole.all().first()
    guesses = 1
    guesses_correct = 0

    if pole_pred.driver == result.driver:
        pole_pred.correct = True
        guesses_correct += 1
        return pole_pred, score_format[1], True

    guesses_dict = {"guesses": guesses, "correct": guesses_correct}
    return pole_pred, 0, False, guesses_dict


def compare_race(results, pred, score_format):
    p_preds = pred.predicted_positions.all()
    points = 0
    update_p_preds = []
    changed = False
    guesses = 0
    guesses_correct = 0

    for idx, p_pos in enumerate(p_preds):
        if results[idx] == p_pos.driver.number:
            key = str(idx + 1)  #Idx starts from 0, score_format from 1
            points += score_format[key]
            p_pos.correct = True
            update_p_preds.append(p_pos)

            guesses_correct += 1
            changed = True
        
        guesses += 1

    guesses_dict = {"guesses": guesses, "correct": guesses_correct}
    return update_p_preds, points, changed, guesses_dict


def compare_session_preds(session, results, score_format, s_scores, users_stats):
    session_type = session.session_type
    updated_preds = []
    updated_p_preds = []

    for pred in session.preds:
        user_season_score = pred.season_score
        user = user_season_score.user
        user_best_pred = user.best_prediction

        if session_type == "Qualifying":
            pole_pred, points, changed, guesses = (
                compare_qualifying(results, pred, score_format)
            )
            updated_p_preds.append(pole_pred)

        else:
            append_updated_p_preds, points, changed, guesses = (
                compare_race(results, pred, score_format)
            )
            updated_p_preds.extend(append_updated_p_preds)

        if changed:
            pred.points_scored += Decimal(str(points))

            s_scores[user_season_score] += points
            updated_preds.append(pred)

        if user not in users_stats:
            users_stats[user] = guesses
            users_stats[user].update({"best_pred": user_best_pred})
        else:
            users_stats[user]["guesses"] += guesses["guesses"]
            users_stats[user]["correct"] += guesses["correct"]

        if user_best_pred:
            if user_best_pred.points_scored < points:
                users_stats[user]["best_pred"] = pred
        else:
            users_stats[user]["best_pred"] = pred

    return updated_preds, updated_p_preds, s_scores, users_stats
