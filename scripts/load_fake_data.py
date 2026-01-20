##########################################################

import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Djesaja_LiveBackstage.settings")

import django

django.setup()

from accounts.models import User
from managers.models import Manager
from creators.models import Creator
from api.models import ReportingMonth
from django.utils import timezone
import re

current_month = timezone.now().strftime("%Y%m")


# ----------------- Helper function -----------------
def get_reporting_month_from_code(code: str):
    """
    code: '202512' or '202601'
    Returns ReportingMonth instance
    """
    report_month, _ = ReportingMonth.objects.get_or_create(code=str(code))
    return report_month


def parse_money(value: str) -> float:
    if not value:
        return 0.0
    m = re.search(r"([\d,]+\.?\d*)", value)
    return float(m.group(1).replace(",", "")) if m else 0.0


def parse_diamonds(value: str) -> int:
    if not value:
        return 0

    match = re.search(r"([\d,]+)", value)
    if not match:
        return 0

    return int(match.group(1).replace(",", ""))


def parse_milestones(value: str) -> list:
    if not value or "No" in value:
        return []
    return [v.strip() for v in value.split("\n") if v.strip()]


# ----------------- Main function -----------------
def save_scrape_data(data, month_code=None):
    """
    month_code: optional 'YYYYMM'. Default: current month
    """
    if month_code is None:
        month_code = timezone.now().strftime("%Y%m")

    report_month = get_reporting_month_from_code(month_code)

    for m in data:
        # ---------------- Manager User ----------------
        manager_username = m["Creator Network manager"]
        user_m, created = User.objects.get_or_create(
            username=manager_username,
            defaults={"role": "MANAGER"},
        )
        # Manager user
        if user_m.name != manager_username:
            user_m.name = manager_username
            user_m.save(update_fields=["name"])

        # ✅ Change 1: set_password for login
        if created:
            user_m.set_password(manager_username)
            user_m.save()

        # ---------------- Manager Table ----------------
        manager, _ = Manager.objects.update_or_create(
            user=user_m,
            report_month=report_month,
            defaults={
                "eligible_creators": int(m["Eligible creators"]),
                "estimated_bonus_contribution": parse_money(
                    m["Estimated bonus contribution"]
                ),
                "diamonds": parse_diamonds(m["Diamonds"]),
                "M_0_5": int(m.get("M0.5", 0)),
                "M1": int(m.get("M1", 0)),
                "M2": int(m.get("M2", 0)),
                "M1R": int(m.get("M1R", 0)),
            },
        )

        # ---------------- Creators ----------------
        for c in m["creators"]:
            creator_name = c["Creator"]
            if not creator_name or creator_name.strip() == "-":
                continue

            user_c, created = User.objects.get_or_create(
                username=creator_name,
                defaults={"role": "CREATOR"},
            )
            # Creator user
            if user_c.name != creator_name:
                user_c.name = creator_name
                user_c.save(update_fields=["name"])

            # ✅ Change 1: set_password for login
            if created:
                user_c.set_password(creator_name)
                user_c.save()

            # numeric cleanup
            try:
                live_duration = float(c["LIVE duration"].split()[0])
            except:
                live_duration = 0.0

            try:
                valid_go_live_days = int(c["Valid go LIVE days"].split()[0])
            except:
                valid_go_live_days = 0

            # ---------------- Handle manager switch ----------------
            creator_obj, _ = Creator.objects.update_or_create(
                user=user_c,
                report_month=report_month,
                defaults={
                    "manager": manager,
                    "estimated_bonus_contribution": parse_money(
                        c["Estimated bonus contribution"]
                    ),
                    "achieved_milestones": parse_milestones(c["Achieved milestones"]),
                    "diamonds": parse_diamonds(c["Diamonds"]),
                    "valid_go_live_days": valid_go_live_days,
                    "live_duration": live_duration,
                },
            )

    print(f"✅ Fake data inserted/updated for month {month_code}")


# ----------------- Load JSON -----------------
with open("fake_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ----------------- Run -----------------

save_scrape_data(data, month_code=current_month)
