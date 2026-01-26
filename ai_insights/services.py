from managers.models import Manager
from creators.models import Creator
from api.models import ReportingMonth

import requests
from datetime import datetime, timedelta


# ekhane ami ai te request korbo. and ai theke asa response amr model onojayi kore db te insert korbo.
# 1️⃣ Helpers: Month code / auto mode
def get_month_code(prev_month=False):
    today = datetime.today()
    if prev_month:
        # previous month
        first_day_this_month = today.replace(day=1)
        last_month = first_day_this_month - timedelta(days=1)
        return last_month.strftime("%Y%m")
    # current month
    return today.strftime("%Y%m")


def auto_run_mode():
    today = datetime.today()
    if today.day == 1:  # মাসের প্রথম দিন → month_start
        return "month_start", get_month_code(prev_month=True)
    else:
        return "daily", get_month_code(prev_month=False)


# 2️⃣ Collect managers and creators


def collect_managers_and_creators(month_code: str):
    report_month = ReportingMonth.objects.get(code=month_code)

    managers_qs = Manager.objects.filter(report_month=report_month).select_related(
        "user"
    )
    creators_qs = Creator.objects.filter(report_month=report_month).select_related(
        "user", "manager", "manager__user"
    )

    managers = []
    for m in managers_qs:
        managers.append(
            {
                "id": m.id,
                "user": {
                    "username": m.user.username,
                    "role": "MANAGER",
                },
                "eligible_creators": m.eligible_creators,
                "estimated_bonus_contribution": float(m.estimated_bonus_contribution),
                "diamonds": m.diamonds,
                "M_0_5": m.M_0_5,
                "M1": m.M1,
                "M2": m.M2,
                "M1R": m.M1R,
                "created_at": m.created_at.isoformat(),
            }
        )

    creators = []
    for c in creators_qs:
        creators.append(
            {
                "user": {
                    "username": c.user.username,
                    "role": "CREATOR",
                },
                "manager": c.manager.id if c.manager else None,
                "manager_username": c.manager.user.username if c.manager else None,
                "estimated_bonus_contribution": float(c.estimated_bonus_contribution),
                "achieved_milestones": c.achieved_milestones or [],
                "diamonds": c.diamonds,
                "valid_go_live_days": c.valid_go_live_days,
                "live_duration": float(c.live_duration),
                "created_at": c.created_at.isoformat(),
            }
        )

    return managers, creators


# 3️⃣ Build AI Snapshot
def build_ai_snapshot(month_code: str, mode: str) -> dict:
    managers, creators = collect_managers_and_creators(month_code)

    if mode == "month_start":
        return {
            "snapshot_time": month_code,
            "previous_creators": creators,
            "previous_managers": managers,
        }

    if mode == "daily":
        return {
            "snapshot_time": month_code,
            "creators": creators,
            "managers": managers,
        }

    raise ValueError("Invalid AI snapshot mode")


# 4️⃣ Run AI service
def run_ai_service(month_code: str, mode: str):
    snapshot = build_ai_snapshot(month_code, mode)

    if mode == "month_start":
        url = "http://172.252.13.97:8026/v1/month-start/run"
    elif mode == "daily":
        url = "http://172.252.13.97:8026/v1/daily/run"
    else:
        raise ValueError("Invalid AI mode")

    response = requests.post(url, json=snapshot)

    print(f"[{mode.upper()}] STATUS:", response.status_code)
    print(f"[{mode.upper()}] TEXT:", response.text)

    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


# 5️⃣ Auto-run helper
def run_ai_full_cycle():
    mode, month_code = auto_run_mode()
    snapshot = build_ai_snapshot(month_code, mode)
    response = run_ai_service(month_code, mode)

    if mode == "month_start":
        store_monthly_ai_response(response, month_code)
    elif mode == "daily":
        store_daily_ai_response(response, month_code)


# -----------------------------
# ✅ USAGE:
# -----------------------------
# 1️⃣ Run manually
# run_ai_auto()

# 2️⃣ Or schedule via cron / Windows Task Scheduler
# services.py e add korte hobe

from django.db import transaction
from django.utils import timezone
from ai_insights.models import AITarget, AIMessage, AIDailySummary, AIScenario, AIMetric
from accounts.models import User


@transaction.atomic
def store_monthly_ai_response(response: dict, month_code: str):
    report_month = ReportingMonth.objects.get(code=month_code)

    # ----- AITarget -----
    creator_targets = response.get("creator_targets", {}).get("creators", [])
    user_map = {
        u.username: u
        for u in User.objects.filter(
            username__in=[c["creator_id"] for c in creator_targets]
        )
    }
    targets_to_create = [
        AITarget(
            user=user_map[c["creator_id"]],
            report_month=report_month,
            target_milestone=c["target"]["milestone"],
            target_diamonds=c["target"]["diamonds"],
            reward_status=c.get("reward_status"),
            expires_at=timezone.now() + timedelta(days=30),
        )
        for c in creator_targets
        if c["creator_id"] in user_map
    ]
    AITarget.objects.bulk_create(targets_to_create, ignore_conflicts=True)

    # ----- AIMessage -----
    messages = response.get("welcome_messages", {}).get("messages", [])
    user_ids = {
        u.username: u
        for u in User.objects.filter(username__in=[m["id"] for m in messages])
    }

    msgs_to_create = [
        AIMessage(
            user=user_ids.get(m["id"]),
            message_type=m["type"],
            message=m["message"],
            expires_at=timezone.now() + timedelta(days=30),
        )
        for m in messages
    ]
    AIMessage.objects.bulk_create(msgs_to_create)


@transaction.atomic
def store_daily_ai_response(response: dict, month_code: str):
    report_month = ReportingMonth.objects.get(code=month_code)
    creators = response.get("creator", {}).get("creators", [])
    user_map = {
        u.username: u
        for u in User.objects.filter(username__in=[c["creator_id"] for c in creators])
    }

    daily_summaries = []
    scenarios = []
    metrics = []

    for c in creators:
        user = user_map.get(c["creator_id"])
        if not user:
            continue

        alert = c.get("alert", {})
        daily_summaries.append(
            AIDailySummary(
                user=user,
                report_month=report_month,
                summary=c.get("summary"),
                reason=c.get("reason"),
                suggested_actions=c.get("suggested_actions", []),
                alert_type=alert.get("type"),
                priority=alert.get("priority"),
                status=alert.get("status"),
            )
        )
        scenarios.append(
            AIScenario(
                user=user,
                report_month=report_month,
                data=c.get("scenarios", {}),
            )
        )
        for k, v in c.get("metrics", {}).items():
            metrics.append(
                AIMetric(
                    user=user,
                    report_month=report_month,
                    key=k,
                    value=v,
                )
            )

    for obj in daily_summaries:
        AIDailySummary.objects.update_or_create(
            user=obj.user,
            report_month=report_month,
            defaults={
                "summary": obj.summary,
                "reason": obj.reason,
                "suggested_actions": obj.suggested_actions,
                "alert_type": obj.alert_type,
                "priority": obj.priority,
                "status": obj.status,
            },
        )

    for obj in scenarios:
        AIScenario.objects.update_or_create(
            user=obj.user,
            report_month=report_month,
            defaults={"data": obj.data},
        )

    for m in metrics:
        AIMetric.objects.update_or_create(
            user=m.user,
            report_month=report_month,
            key=m.key,
            defaults={"value": m.value},
        )

    admin_data = response.get("admin")

    if admin_data:
        admin_user = User.objects.filter(username="admin").first()
        if admin_user:
            AIDailySummary.objects.update_or_create(
                user=admin_user,
                report_month=report_month,
                defaults={
                    "summary": admin_data.get("summary"),
                    "reason": admin_data.get("reason"),
                    "suggested_actions": admin_data.get("suggested_actions", []),
                },
            )

            for k, v in admin_data.get("metrics", {}).items():
                AIMetric.objects.update_or_create(
                    user=admin_user,
                    report_month=report_month,
                    key=k,
                    defaults={"value": v},
                )
    for m in response.get("manager", {}).get("managers", []):
        user = User.objects.filter(username=m["manager_name"]).first()
        if not user:
            continue

        AIDailySummary.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={
                "summary": m.get("summary"),
                "reason": m.get("reason"),
                "suggested_actions": m.get("suggested_actions", []),
            },
        )
