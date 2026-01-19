# managers/models.py
from django.db import models
from accounts.models import User
from api.models import ReportingMonth


class Manager(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="manager_profile"
    )
    report_month = models.ForeignKey(
        ReportingMonth,
        on_delete=models.CASCADE,
        related_name="month_managers",
    )
    eligible_creators = models.IntegerField(default=0)
    estimated_bonus_contribution = models.CharField(max_length=250, blank=True)
    diamonds = models.CharField(max_length=250, blank=True)
    M_0_5 = models.IntegerField(default=0)
    M1 = models.IntegerField(default=0)
    M2 = models.IntegerField(default=0)
    M1R = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            "user",
            # "month",
        )  # same manager duplicate jeno na hoy

    def __str__(self):
        return f"{self.name} - {self.report_month.code}"
