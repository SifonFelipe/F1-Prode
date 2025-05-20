from datetime import datetime, timezone

FNAME_TO_CLASS = {
    "Red Bull Racing": "red-bull",
    "Racing Bulls": "racing-bulls",
    "Haas F1 Team": "haas",
    "Kick Sauber": "sauber",
    "Williams": "williams",
    "Mercedes": "mercedes",
    "McLaren": "mclaren",
    "Ferrari": "ferrari",
    "Aston Martin": "aston-martin",
    "Alpine": "alpine"
}

PRED_POINTS_BY_POSITION = {
    1: 5,
    2: 3,
    3: 2,
    4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1,
    11: 0.5, 12: 0.5, 13: 0.5, 14: 0.5, 15: 0.5,
    16: 0.25, 17: 0.25, 18: 0.25, 19: 0.25, 20: 0.25
}

SPRINT_PRED_POINTS_BY_POSITION = {
    1: 2.5,
    2: 1.5,
    3: 1,
    4: 0.5, 5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5, 9: 0.5, 10: 0.5,
    11: 0.25, 12: 0.25, 13: 0.25, 14: 0.25, 15: 0.25,
    16: 0.10, 17: 0.10, 18: 0.10, 19: 0.10, 20: 0.10
}

PRED_POLE_POINTS = 4

DRIVERS_BY_RACE = 20

CURRENT_SEASON = 2025

TIME_LIMIT_CHAMPIONS_PRED = datetime(CURRENT_SEASON, 6, 15, tzinfo=timezone.utc)