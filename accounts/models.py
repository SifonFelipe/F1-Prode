from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime
from django.db.models import Sum

class CustomUser(AbstractUser):
    @property   #property hace que sea un atributo de la clase. No hace falta llamar a CustomUser.friends(), solo a CustomUser.friends
    def friends(self):
        sent = CustomUser.objects.filter(
            received_requests__from_user=self,
            received_requests__is_accepted=True
        )
        received = CustomUser.objects.filter(
            sent_requests__to_user=self,
            sent_requests__is_accepted=True
        )
        return sent.union(received)

class FriendRequest(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_requests', on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def accept(self):
        self.is_accepted = True
        self.save()

    def reject(self):
        self.delete()

    def save(self, *args, **kwargs):
        if self.from_user == self.to_user:
            raise ValueError("No podés enviarte una solicitud a vos mismo.")
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friend_request')
        ]

    def __str__(self):
        return f"{self.from_user} ➜ {self.to_user} ({'aceptada' if self.is_accepted else 'pendiente'})"