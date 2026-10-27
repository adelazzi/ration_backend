from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Users table: login is by email; password is stored hashed by Django."""

    class Role(models.TextChoices):
        MANAGER = 'manager', 'Manager'
        ACCOUNTANT = 'accountant', 'Accountant'
        CREATOR = 'creator', 'Creator'

    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CREATOR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.full_name or self.username
