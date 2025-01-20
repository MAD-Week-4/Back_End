# accounts/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    assets = models.FloatField(default=1000000)   # 랭크 점수

    def __str__(self):
        return f"{self.user.username}의 프로필"