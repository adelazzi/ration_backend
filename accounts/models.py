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

    # Role rules: managers add, edit and remove everything; accountants review prices;
    # creators only read approved project reports. Superusers can do everything.

    @property
    def is_manager(self):
        return self.is_superuser or self.role == self.Role.MANAGER

    @property
    def can_review_prices(self):
        return self.is_superuser or self.role == self.Role.ACCOUNTANT

    @property
    def can_view_config(self):
        return self.is_manager or self.can_review_prices

    @property
    def sees_only_approved_projects(self):
        return not (self.is_manager or self.can_review_prices)
