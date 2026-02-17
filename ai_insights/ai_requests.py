import json
import requests
from collections import defaultdict
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


# ----------------- Step 2: Helpers for Chunking -----------------


def group_creators_by_manager(creators):
    grouped = defaultdict(list)
    for c in creators:
        manager_id = c["manager"]
        grouped[manager_id].append(c)
    return grouped


# ----------------- Step 3: AI Request -----------------

AI_ENDPOINTS = {
    "daily": "http://172.252.13.97:8026/v1/daily/run",
    "month_start": "http://172.252.13.97:8026/v1/month-start/run",
}


def send_ai_request(payload: dict, mode: str):
    if mode not in AI_ENDPOINTS:
        raise ValueError("Mode must be 'daily' or 'month_start'")

    AI_ENDPOINT = AI_ENDPOINTS[mode]
    headers = {"Content-Type": "application/json"}

    print("📤 Sending AI request...")
    response = requests.post(AI_ENDPOINT, headers=headers, json=payload)

    print(f"📥 AI Response ({mode}) received")
    return response.json()


# ----------------- Step 4: DB Save Logic (as-is) -----------------


def save_monthly_response_to_db(response, report_month):
    expires_at = timezone.now() + timedelta(days=33)
    msg_expires_at = timezone.now() + timedelta(days=3)

    for c in response["creator_targets"]["creators"]:
        user = User.objects.get(username=c["creator_id"])
        AITarget.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={
                "target_milestone": c["target"]["milestone"],
                "target_diamonds": c["target"]["diamonds"],
                "reward_status": c.get("reward_status"),
                "expires_at": expires_at,
            },
        )

    for m in response["manager_targets"]["managers"]:
        user = User.objects.get(username=m["manager_username"])
        AIManagerTarget.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={
                "team_target_diamonds": m["team_target_diamonds"],
                "expires_at": expires_at,
            },
        )

    for msg in response["welcome_messages"]["messages"]:
        user = User.objects.filter(username=msg["id"]).first()
        AIMessage.objects.update_or_create(
            user=user,
            message_type=msg["type"],
            defaults={"message": msg["message"], "expires_at": msg_expires_at},
        )


def save_daily_response_to_db(response, report_month):
    for c in response["creator"]["creators"]:
        user = User.objects.get(username=c["creator_id"])
        AIDailySummary.objects.update_or_create(
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

        AIScenario.objects.update_or_create(
            user=user, report_month=report_month, defaults={"data": c.get("scenarios")}
        )

        AIMetric.objects.update_or_create(
            user=user,
            report_month=report_month,
            defaults={"data": c.get("metrics", {})},
        )

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

    admin_data = response.get("admin")
    if admin_data:
        admin_user = User.objects.get(username="admin")
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
        if admin_data.get("metrics"):
            AIMetric.objects.update_or_create(
                user=admin_user,
                report_month=report_month,
                defaults={"data": admin_data.get("metrics")},
            )


# ----------------- Step 5: Chunked Processing -----------------


def run_chunked_ai(month_code: str, mode: str):
    managers, creators = collect_managers_and_creators(month_code)
    creators_by_manager = group_creators_by_manager(creators)
    # report_month = ReportingMonth.objects.get(code=month_code)
    report_month, _ = ReportingMonth.objects.get_or_create(code=month_code)

    for manager in managers:
        manager_id = manager["id"]
        batch_creators = creators_by_manager.get(manager_id, [])

        # Build mode-specific payload
        if mode == "month_start":
            payload = {
                "snapshot_time": month_code,
                "previous_managers": [manager],
                "previous_creators": batch_creators,
            }
        else:  # daily
            payload = {
                "snapshot_time": month_code,
                "managers": [manager],
                "creators": batch_creators,
            }

        print(
            f"\n🚀 Sending AI request for manager {manager['user']['username']} "
            f"with {len(batch_creators)} creators..."
        )

        try:
            response = send_ai_request(payload, mode)
        except Exception as e:
            print(f"❌ Failed for manager {manager['user']['username']}: {e}")
            continue

        # Save response immediately
        if mode == "month_start":
            save_monthly_response_to_db(response, report_month)
        else:
            save_daily_response_to_db(response, report_month)

        print(f"✅ Completed for manager {manager['user']['username']}")


# ----------------- Step 6: Test Run -----------------

if __name__ == "__main__":
    month_code = "202601"
    mode = "month_start"  # or 'daily'

    run_chunked_ai(month_code, mode)
