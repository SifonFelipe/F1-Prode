from django.db import models
from django.conf import settings
from datetime import datetime

year = datetime.now().year

class Driver(models.Model):
    """
    Drivers model.
    A driver for year.
    """
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    number = models.IntegerField()
    team_name = models.CharField(max_length=60)
    country = models.CharField(max_length=70, null=True, blank=True)
    headshot = models.URLField(max_length=500)
    points = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    year = models.IntegerField(default=datetime.now().year)

    class Meta:
        ordering = ["-points", "number"]

    def __str__(self):
        return f"{self.last_name} - {self.year}"
    
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
    location = models.CharField(max_length=100) #country or city
    country = models.CharField(max_length=100)
    date = models.DateField()
    n_round = models.IntegerField(unique=True, null=True)
    year = models.IntegerField()
    event_format = models.CharField(max_length=50, choices=EVENT_TYPES, default="testing")
    ended = models.BooleanField(default=False)

    class Meta:
        ordering = ["date"]
        indexes = [
            models.Index(fields=['date', 'name', 'country'])
        ]

    def __str__(self):
        return f"{self.name} - {self.location} - {self.date}"
    
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

    grand_prix = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name='sessions')
    session_type = models.CharField(max_length=50, choices=SESSION_TYPES)
    session_date = models.DateTimeField()  # Fecha y hora de la sesión

    def __str__(self):
        return f"{self.session_type} - {self.grand_prix.name}"

    
class RacingTeam(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField(default=year)
    driver1 = models.ForeignKey(Driver, blank=True, null=True, on_delete=models.DO_NOTHING, related_name="first_driver")
    driver2 = models.ForeignKey(Driver, blank=True, null=True, on_delete=models.DO_NOTHING, related_name="second_driver")
    points = models.DecimalField(default=0, decimal_places=2, max_digits=8)

    def __str__(self):
        return f"{self.name} - {self.year}"
    
class Prediction(models.Model):
    """
    Prediction model.
    It works as a manager for the predictions of a user for a session.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Relación con el usuario
    session = models.ForeignKey(Session, on_delete=models.CASCADE)  # Relación con el Gran Premio
    points_scored = models.DecimalField(default=0, decimal_places=2, max_digits=6)
    
    class Meta:
        ordering = ["-points_scored", "user"]

    def __str__(self):
        return f"Prediction by {self.user.username} for {self.session.grand_prix.name}" 

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
        return f"{self.driver.first_name} {self.driver.last_name} - Predicted Position: {self.position}"
    
class PredictedPole(models.Model):
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='predicted_pole')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True)
    correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['prediction'], name='unique_prediction_for_pole')
        ]

    def __str__(self):
        return f"{self.driver} for Pole Position in {self.prediction.session.grand_prix.name}"
class Result(models.Model):
    """
    Results model.
    It contains the result for each driver in a session.
    """
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
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
        return f"{self.session} - {self.driver} - {self.position}"
    
class ResultPole(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    lap_time = models.DurationField(blank=True, null=True)
    for_which_team = models.ForeignKey(RacingTeam, on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return f"Pole Position for {self.driver.last_name} in {self.session.grand_prix.name}"