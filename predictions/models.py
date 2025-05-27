from django.db import models
from django.conf import settings
from datetime import timedelta

class SeasonSettings(models.Model):
    season = models.IntegerField()
    amount_drivers = models.IntegerField()
    amount_teams = models.IntegerField()
    race_points_pred = models.JSONField()
    sprint_points_pred = models.JSONField()
    qualy_points_pred = models.IntegerField()

    def __str__(self):
        return f"{self.season}"


class RacingTeam(models.Model):
    name = models.CharField(max_length=100)
    season = models.ForeignKey(SeasonSettings, on_delete=models.DO_NOTHING, related_name='racing_teams')
    points = models.DecimalField(default=0, decimal_places=2, max_digits=8)

    class Meta:
        ordering = ['-points', 'name']

    def __str__(self):
        return f"[{self.season}] {self.name}"


class Driver(models.Model):
    """
    Drivers model.
    A driver for year.
    """
    
    season = models.ForeignKey(SeasonSettings, on_delete=models.DO_NOTHING, related_name='drivers')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    number = models.IntegerField()
    racing_team = models.ForeignKey(RacingTeam, on_delete=models.DO_NOTHING, related_name='drivers')
    country = models.CharField(max_length=70, null=True, blank=True)
    headshot = models.URLField(max_length=500)
    points = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-points", "number"]

    def __str__(self):
        return f"[{self.season}] {self.first_name} {self.last_name} ( {self.number} )"


class GrandPrix(models.Model):
    """
    GPs model.
    """

    EVENT_TYPES = [
        ("testing", "testing"),
        ("conventional", "normal"),
        ("sprint_qualifying", "sprint"),
    ]

    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)  # country or city
    country = models.CharField(max_length=100)
    date = models.DateField()
    start_date = models.DateField()
    n_round = models.IntegerField(unique=True, null=True)
    season = models.ForeignKey(SeasonSettings, on_delete=models.DO_NOTHING, related_name="gps")
    event_format = models.CharField(max_length=50, choices=EVENT_TYPES, default="testing")
    ended = models.BooleanField(default=False)
    lineup_associated = models.BooleanField(default=False)

    class Meta:
        ordering = ["date"]
        indexes = [
            models.Index(fields=['date', 'name', 'country'])
        ]

    def __str__(self):
        return f"[{self.season}] {self.name} - {"Ended" if self.ended else "Not Ended"}"


class Session(models.Model):
    """
    Sessions model.
    """
    SESSION_TYPES = [
        ('Practice 1', 'FP1'),
        ('Practice 2', 'FP2'),
        ('Practice 3', 'FP3'),
        ('Qualifying', 'Q'),
        ('Sprint Qualifying', 'SQ'),
        ('Sprint', 'S'),
        ('Race', 'Race'),
    ]

    STATES = [
        ('NOT FINISHED', 'NF'), #waiting for results
        ('FINISHED WAITING COMPARE', 'FWC'), #finished but not compared with predictions
        ('FINISHED', 'F') #finished everything
    ]

    grand_prix = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name='sessions')
    session_type = models.CharField(max_length=50, choices=SESSION_TYPES)
    session_date = models.DateTimeField()
    state = models.CharField(max_length=50, choices=STATES, default="NF")

    class Meta:
        ordering = ['session_date']

    def __str__(self):
        return f"[{self.grand_prix.season} - {self.grand_prix.name}] {self.session_type} - {self.state}"


class RaceLineUp(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="drivers")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="participations")
    team = models.ForeignKey(RacingTeam, on_delete=models.CASCADE, related_name="participations")

    participated = models.BooleanField(default=True)

    class Meta:
        unique_together = ("session", "driver")

    def __str__(self):
        return f"{self.session} - {self.driver} - {self.team}"

class ChampionPrediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    season = models.ForeignKey(SeasonSettings, on_delete=models.DO_NOTHING, related_name="champion_preds")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    team = models.ForeignKey(RacingTeam, on_delete=models.CASCADE)

    def __str__(self):
        return f"[{self.season.season}] {self.user} {self.team.name[:3].upper()} {self.driver.last_name[:3].upper()}"


class Prediction(models.Model):
    """
    Prediction model.
    It works as a manager for the predictions of a user for a session.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="predictions")
    points_scored = models.DecimalField(default=0, decimal_places=2, max_digits=6)

    @property
    def pole(self):
        return self.predicted_pole.first()
    class Meta:
        ordering = ["-points_scored", "user"]
        constraints = [
            models.UniqueConstraint(fields=['user', 'session'], name='unique_prediction_per_user_per_session')
        ]

    def __str__(self):
        return f"[{self.session.grand_prix.season} - {self.session.grand_prix.name}] Prediction by {self.user.username} for {self.session.session_type}" 


class PredictedPosition(models.Model):
    """
    Predicted Positions model.
    It contains the prediction for each driver and is related to prediction.
    """
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='predicted_positions')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    position = models.IntegerField()
    correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('prediction', 'driver')  # Un usuario solo puede predecir una posición por piloto
        indexes = [
            models.Index(fields=['prediction', 'driver']),  # Índice para optimizar consultas
            models.Index(fields=['position']),  # Índice para mejorar las consultas por posición
        ]

        ordering = ["position"]

    def __str__(self):
        return f"[{self.prediction.session.grand_prix.season} - {self.prediction.session.grand_prix.name} - {self.prediction.session.session_type}] {self.position} - {self.driver.last_name}"


class PredictedPole(models.Model):
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='predicted_pole')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True)
    correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['prediction'], name='unique_prediction_for_pole')
        ]

    def __str__(self):
        return f"[{self.prediction.session.grand_prix.season} - {self.prediction.session.grand_prix.name} - {self.prediction.session.session_type}] POLE - {self.driver.last_name}"


class Result(models.Model):
    """
    Results model.
    It contains the result for each driver in a session.
    """
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="race_results")
    position = models.IntegerField()
    laps_completed = models.IntegerField()
    fastest_lap = models.DurationField(blank=True, null=True)
    fastest_lap_session = models.BooleanField(default=False)
    disqualified = models.BooleanField(default=False)
    for_which_team = models.ForeignKey(RacingTeam, on_delete=models.DO_NOTHING, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['driver', 'session']),  # Índice para optimizar consultas por piloto y sesión
            models.Index(fields=['position']),  # Índice para optimizar consultas por posición
        ]

        ordering = ["position"]

    def __str__(self):
        return f"[{self.session.grand_prix.season} - {self.session.grand_prix.name} - {self.session.session_type}] {self.position} - {self.driver.last_name}"


class ResultPole(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="pole_result")
    lap_time = models.DurationField(blank=True, null=True)
    for_which_team = models.ForeignKey(RacingTeam, on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return f"[{self.session.grand_prix.season} - {self.session.grand_prix.name} - {self.session.session_type}] POLE - {self.driver.last_name}"