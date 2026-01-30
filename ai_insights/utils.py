from django.utils import timezone
from ai_insights.models import (
    AIMessage,
    AIDailySummary,
    AIScenario,
    AIMetric,
)
from api.models import ReportingMonth
from datetime import datetime, timedelta
from api.models import ReportingMonth
from django.utils.timezone import localtime


def get_current_month():
    code = datetime.now().strftime("%Y%m")
    return ReportingMonth.objects.get(code=code)


def get_previous_month():
    first_day = datetime.now().replace(day=1)
    prev_month = first_day - timedelta(days=1)
    return ReportingMonth.objects.get(code=prev_month.strftime("%Y%m"))


def normalize_actions(actions):
    if not actions:
        return []
    if isinstance(actions, list):
        return actions
    return [actions]


def format_datetime(dt, time_format_24=True):
    """
    Convert a datetime to dict with 'date' and 'time'.

    dt: datetime object
    time_format_24: True -> 24-hour format, False -> 12-hour with AM/PM
    """
    if not dt:
        return {"date": None, "time": None}

    local_dt = localtime(dt)
    date_str = local_dt.strftime("%Y-%m-%d")

    if time_format_24:
        time_str = local_dt.strftime("%H:%M:%S")
    else:
        time_str = local_dt.strftime("%I:%M %p")

    return {"date": date_str, "time": time_str}


def get_common_ai_data(user, report_month):
    msg = (
        AIMessage.objects.filter(user=user, expires_at__gte=timezone.now())
        .order_by("-created_at")
        .first()
    )

    summary = AIDailySummary.objects.filter(
        user=user, report_month=report_month
    ).first()

    scenario = AIScenario.objects.filter(user=user, report_month=report_month).first()

    metric = AIMetric.objects.filter(user=user, report_month=report_month).first()

    return {
        "welcome_msg": {
            "msg_type": msg.message_type if msg else None,
            "msg": msg.message if msg else None,
        },
        "daily_summary": {
            "summary": summary.summary if summary else None,
            "reason": summary.reason if summary else None,
            "suggested_action": (
                normalize_actions(summary.suggested_actions) if summary else []
            ),
            "alert_type": summary.alert_type if summary else None,
            "alert_message": summary.alert_message if summary else None,
            "priority": summary.priority if summary else None,
            "status": summary.status if summary else None,
            "updated_at": format_datetime(summary.updated_at),
        },
        "scenarios": scenario.data if scenario else {},
        "metrics": metric.data if metric else {},
    }


def get_alert_counts(users, report_month):
    qs = AIDailySummary.objects.filter(user__in=users, report_month=report_month)
    high = qs.filter(priority__iexact="high").count()
    low = qs.filter(priority__isnull=True).count()
    return {"high": high, "low": low}
