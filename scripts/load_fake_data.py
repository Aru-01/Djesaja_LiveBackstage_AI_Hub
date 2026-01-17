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
from django.utils import timezone

current_month = timezone.now().strftime("%Y%m")


def save_scrape_data(data, month=current_month):
    for m in data:
        # ---------------- Manager User ----------------
        manager_username = m["Creator Network manager"]
        user_m, created = User.objects.get_or_create(
            username=manager_username,
            defaults={
                "role": "MANAGER",
                "password": manager_username,  # temporary
            },
        )

        # ---------------- Manager Table ----------------
        manager, _ = Manager.objects.update_or_create(
            user=user_m,
            month=month,
            defaults={
                "name": manager_username,
                "eligible_creators": int(m["Eligible creators"]),
                "estimated_bonus_contribution": m["Estimated bonus contribution"],
                "diamonds": m["Diamonds"],
                "M_0_5": int(m.get("M0.5", 0)),
                "M1": int(m.get("M1", 0)),
                "M2": int(m.get("M2", 0)),
                "M1R": int(m.get("M1R", 0)),
            },
        )

        # ---------------- Creators ----------------
        for c in m["creators"]:
            creator_name = c["Creator"]
            if creator_name == "-" or creator_name.strip() == "":
                continue  # skip invalid names

            user_c, created = User.objects.get_or_create(
                username=creator_name,
                defaults={
                    "role": "CREATOR",
                    "password": creator_name,  # temporary
                },
            )

            # clean numeric fields
            live_duration = 0.0
            try:
                live_duration = float(c["LIVE duration"].split()[0])
            except:
                pass

            valid_go_live_days = 0
            try:
                valid_go_live_days = int(c["Valid go LIVE days"].split()[0])
            except:
                pass

            Creator.objects.update_or_create(
                user=user_c,
                manager=manager,
                month=month,
                defaults={
                    "name": creator_name,
                    "estimated_bonus_contribution": c["Estimated bonus contribution"],
                    "achieved_milestones": c["Achieved milestones"],
                    "diamonds": c["Diamonds"],
                    "valid_go_live_days": valid_go_live_days,
                    "live_duration": live_duration,
                },
            )

    print("✅ Scrape data inserted/updated successfully!")


with open("fake_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

save_scrape_data(data, month=current_month)
