from django.db import models
from accounts.models import User
from api.models import ReportingMonth
from managers.models import Manager


class Creator(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="creator_profile"
    )
    manager = models.ForeignKey(
        Manager, on_delete=models.CASCADE, related_name="creators"
    )
    report_month = models.ForeignKey(
        ReportingMonth,
        on_delete=models.CASCADE,
        related_name="month_creators",
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    estimated_bonus_contribution = models.CharField(max_length=100, blank=True)
    achieved_milestones = models.CharField(max_length=100, blank=True)
    diamonds = models.CharField(max_length=100, blank=True)
    valid_go_live_days = models.IntegerField(default=0)
    live_duration = models.FloatField(default=0.0)  # hours
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            "user",
            "manager",
        )  # duplicate check for same manager

    def __str__(self):
        return f"{self.name} ({self.manager.name} - {self.report_month.code})"
