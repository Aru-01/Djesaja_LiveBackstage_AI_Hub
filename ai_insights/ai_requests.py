import json
import requests
from django.utils import timezone
from datetime import timedelta
from managers.models import Manager
from creators.models import Creator
from api.models import ReportingMonth
from accounts.models import User
from ai_insights.models import (
    AITarget,
    AIManagerTarget,
    AIDailySummary,
    AIMessage,
    AIMetric,
    AIScenario,
)

# ----------------- Step 1: Collect DB Data -----------------


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
                    "id": m.user.id,
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
                "id": c.id,
                "user": {
                    "id": c.user.id,
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


# ----------------- Step 2: Build AI snapshot -----------------
def build_ai_snapshot(month_code: str, mode: str):
    managers, creators = collect_managers_and_creators(month_code)

    if mode == "month_start":
        return {
            "snapshot_time": month_code,
            "previous_creators": creators,
            "previous_managers": managers,
        }
    elif mode == "daily":
        return {"snapshot_time": month_code, "creators": creators, "managers": managers}
    else:
        raise ValueError("Invalid mode")


# ----------------- Step 3: Send request to AI -----------------

AI_ENDPOINTS = {
    "daily": "http://172.252.13.97:8026/v1/daily/run",
    "month_start": "http://172.252.13.97:8026/v1/month-start/run",
}


def send_ai_request(payload: dict, mode: str):
    if mode not in AI_ENDPOINTS:
        raise ValueError("Mode must be 'daily' or 'month_start'")

    AI_ENDPOINT = AI_ENDPOINTS[mode]
    headers = {"Content-Type": "application/json"}

    print("📤 Request Payload:")

    response = requests.post(AI_ENDPOINT, headers=headers, json=payload)

    print(f"📥 AI Response ({mode}):")
    # print(response.text)

    return response.json()


#######################################
def save_monthly_response_to_db(response, report_month):
    expires_at = timezone.now() + timedelta(days=40)
    msg_expires_at = timezone.now() + timedelta(days=4)

    # --- creators ---
    for c in response["creator_targets"]["creators"]:
        user = User.objects.get(username=c["creator_id"])
        target, _ = AITarget.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={
                "target_milestone": c["target"]["milestone"],
                "target_diamonds": c["target"]["diamonds"],
                "reward_status": c.get("reward_status"),
                "expires_at": expires_at,
            },
        )

    # --- managers ---
    for m in response["manager_targets"]["managers"]:
        user = User.objects.get(username=m["manager_username"])
        AIManagerTarget.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={"team_target_diamonds": m["team_target_diamonds"]},
        )

    # --- messages ---
    for msg in response["welcome_messages"]["messages"]:
        user = User.objects.filter(username=msg["id"]).first()  # nullable for admin
        AIMessage.objects.update_or_create(
            user=user,
            message_type=msg["type"],
            defaults={"message": msg["message"], "expires_at": msg_expires_at},
        )


def save_daily_response_to_db(response, report_month):

    # --- creators ---
    for c in response["creator"]["creators"]:
        user = User.objects.get(username=c["creator_id"])
        daily, _ = AIDailySummary.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={
                "summary": c.get("summary"),
                "reason": c.get("reason"),
                "suggested_actions": c.get("suggested_actions"),
                "alert_type": c.get("alert", {}).get("type"),
                "alert_message": c.get("alert", {}).get("message"),
                "priority": c.get("alert", {}).get("priority"),
                "status": c.get("alert", {}).get("status"),
            },
        )

        # --- scenarios ---
        AIScenario.objects.update_or_create(
            user=user, report_month=report_month, defaults={"data": c.get("scenarios")}
        )

        # --- metrics ---
        user_metrics = c.get("metrics", {})
        AIMetric.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={"data": user_metrics},
        )

    # --- managers ---
    for m in response["manager"]["managers"]:
        user = User.objects.get(username=m["manager_name"])
        alert = m.get("alert") or {}
        AIDailySummary.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={
                "summary": m.get("summary"),
                "reason": m.get("reason"),
                "suggested_actions": m.get("suggested_actions"),
                "alert_type": alert.get("type"),
                "alert_message": alert.get("message"),
                "priority": alert.get("priority"),
                "status": alert.get("status"),
            },
        )

    # --- admin ---
    admin_data = response.get("admin")
    if admin_data:
        admin_user = User.objects.get(username="admin")

        # daily summary for admin
        AIDailySummary.objects.update_or_create(
            user=admin_user,
            report_month=report_month,
            defaults={
                "summary": admin_data.get("summary"),
                "reason": admin_data.get("reason"),
                "suggested_actions": admin_data.get("suggested_actions"),
                "alert_type": admin_data.get("alert", {}).get("type"),
                "priority": admin_data.get("alert", {}).get("priority"),
                "status": (
                    "active"
                    if admin_data.get("alert", {}).get("active")
                    else "inactive"
                ),
            },
        )

        # metrics for admin
        admin_metrics = admin_data.get("metrics", {})
        if admin_metrics:
            AIMetric.objects.update_or_create(
                user=admin_user,
                report_month=report_month,
                defaults={"data": admin_metrics},
            )


# ----------------- Optional: Test run -----------------
if __name__ == "__main__":
    month_code = "202601"
    mode = "month_start"  # change to 'daily' for daily mode

    payload = build_ai_snapshot(month_code, mode)
    response = send_ai_request(payload, mode)
