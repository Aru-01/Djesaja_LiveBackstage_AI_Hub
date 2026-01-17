# managers/models.py
from django.db import models
from accounts.models import User  

class Manager(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="manager_profile"
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    eligible_creators = models.IntegerField(default=0)
    estimated_bonus_contribution = models.CharField(max_length=250, blank=True)
    diamonds = models.CharField(max_length=250, blank=True)
    M_0_5 = models.IntegerField(default=0)
    M1 = models.IntegerField(default=0)
    M2 = models.IntegerField(default=0)
    M1R = models.IntegerField(default=0)
    month = models.CharField(max_length=6)  # YYYYMM, month-wise data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            "user",
            "month",
        )  # same manager, same month duplicate jeno na hoy

    def __str__(self):
        return f"{self.name} ({self.month})"
