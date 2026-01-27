from django.db import models
from accounts.models import User
from api.models import ReportingMonth


class AIManagerTarget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_month = models.ForeignKey(ReportingMonth, on_delete=models.CASCADE)
    team_target_diamonds = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "report_month")

    def __str__(self):
        return f"{self.user.username} x {self.team_target_diamonds}"


class AITarget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_month = models.ForeignKey(ReportingMonth, on_delete=models.CASCADE)

    target_milestone = models.CharField(max_length=100, null=True, blank=True)
    target_diamonds = models.IntegerField(default=0)
    reward_status = models.CharField(max_length=100, null=True, blank=True)

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "report_month")
        indexes = [
            models.Index(fields=["report_month"]),
        ]

    def __str__(self):
        return f"{self.user.username} x {self.target_diamonds}"


class AIMessage(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    message_type = models.CharField(max_length=150)
    message = models.TextField(blank=True, null=True)

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["expires_at"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} x {self.message_type}"


class AIDailySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_month = models.ForeignKey(ReportingMonth, on_delete=models.CASCADE)

    summary = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    suggested_actions = models.JSONField(default=list, blank=True, null=True)
    alert_type = models.CharField(max_length=50, blank=True, null=True)
    priority = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "report_month")
        indexes = [
            models.Index(fields=["report_month"]),
            models.Index(fields=["priority"]),
        ]

    def __str__(self):
        return f"{self.user.username} x {self.reason}"


class AIScenario(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_month = models.ForeignKey(ReportingMonth, on_delete=models.CASCADE)

    data = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "report_month")
        indexes = [
            models.Index(fields=["report_month"]),
        ]


class AIMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    report_month = models.ForeignKey(ReportingMonth, on_delete=models.CASCADE)
    data = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "report_month")
        indexes = [
            models.Index(fields=["report_month"]),
        ]
