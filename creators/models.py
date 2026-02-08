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

    creator_uid = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    group_name = models.CharField(max_length=255, null=True, blank=True)

    estimated_bonus_contribution = models.FloatField(default=0.0)
    achieved_milestones = models.JSONField(default=list)
    diamonds = models.IntegerField(default=0)
    valid_go_live_days = models.IntegerField(default=0)
    live_duration = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (
            "creator_uid",
            "report_month",
        )  # duplicate check for same creator , same month er jonno

    def __str__(self):
        return f"{self.user.username} ({self.manager.user.username} - {self.report_month.code})"
