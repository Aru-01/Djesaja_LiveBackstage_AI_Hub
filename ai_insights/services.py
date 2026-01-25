from managers.models import Manager
from creators.models import Creator
from api.models import ReportingMonth

import requests
from datetime import datetime, timedelta


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
def run_ai_auto():
    mode, month_code = auto_run_mode()
    print(f"Running AI snapshot automatically: mode={mode}, month_code={month_code}")
    result = run_ai_service(month_code, mode)
    print("AI Response:", result)
    return result


# -----------------------------
# ✅ USAGE:
# -----------------------------
# 1️⃣ Run manually
# run_ai_auto()

# 2️⃣ Or schedule via cron / Windows Task Scheduler
