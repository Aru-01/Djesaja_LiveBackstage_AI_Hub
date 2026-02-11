import sys
import os
import re
from django.db import transaction
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Djesaja_LiveBackstage.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django

django.setup()

from accounts.models import User
from managers.models import Manager
from creators.models import Creator
from api.models import ReportingMonth
from scripts.scraper import scrape_dashboard


# ------------------ Helpers ------------------
def safe_int(val):
    try:
        if val is None:
            return 0
        val = str(val).replace(",", "").strip()
        if not val or val in ["-", "—"]:
            return 0
        return int(float(val))
    except:
        return 0


def parse_money(value):
    if not value:
        return 0.0
    m = re.search(r"([\d,]+\.?\d*)", value)
    return float(m.group(1).replace(",", "")) if m else 0.0


def parse_diamonds(value):
    if not value:
        return 0
    m = re.search(r"([\d,]+)", value)
    return int(m.group(1).replace(",", "")) if m else 0


def parse_milestones(value):
    if not value or "No" in value:
        return []
    return [v.strip() for v in value.split("\n") if v.strip()]


def parse_float(value):
    if not value:
        return 0.0
    # Remove any non-digit/non-dot characters
    value = re.sub(r"[^\d.]+", "", str(value))
    try:
        return float(value)
    except:
        return 0.0


def parse_days(value):
    if not value:
        return 0
    m = re.search(r"(\d+)", str(value))
    return int(m.group(1)) if m else 0


def get_reporting_month(code):
    rm, _ = ReportingMonth.objects.get_or_create(code=str(code))
    return rm


# ------------------ User Management ------------------
def get_or_create_user_by_uid_or_username(
    *, uid=None, username=None, role=None, name=None, email=None
):
    """
    Handles both Manager and Creator creation or retrieval.
    Ensures unique username and avoids duplicate emails.
    """
    if not uid and not username:
        print(f"❌ Skipping user because UID and username are missing")
        return None, False

    # Try find by UID first
    user = User.objects.filter(uid=uid).first() if uid else None

    # Then try find by username if not found
    if not user and username:
        user = User.objects.filter(username=username).first()

    # Update existing user if needed
    if user:
        updated = False
        if username and user.username != username:
            # চেক করো যে username clash হচ্ছে কি না
            if not User.objects.filter(username=username).exclude(pk=user.pk).exists():
                user.username = username
                updated = True
            else:
                # যদি clash হয়, তাহলে unique বানাও
                base = username
                counter = 1
                while (
                    User.objects.filter(username=f"{base}_{counter}")
                    .exclude(pk=user.pk)
                    .exists()
                ):
                    counter += 1
                user.username = f"{base}_{counter}"
                updated = True
        if uid and not user.uid:
            user.uid = uid
            updated = True
        if role and user.role != role:
            user.role = role
            updated = True
        if name and getattr(user, "name", None) != name:
            user.name = name
            updated = True
        if email and not user.email:
            # Only assign email if it's unique
            if not User.objects.filter(email=email).exists():
                user.email = email
                user.email_verified = True
                updated = True

        if updated:
            user.save()
        return user, False

    # Create new user
    original_username = username or f"unknown_{uid}"
    unique_username = original_username
    counter = 1
    while User.objects.filter(username=unique_username).exists():
        unique_username = f"{original_username}_{counter}"
        counter += 1

    user = User.objects.create(
        username=unique_username,
        uid=uid,
        role=role,
        name=name,
        email=(
            email if email and not User.objects.filter(email=email).exists() else None
        ),
        email_verified=bool(email),
    )
    user.set_password("1234")
    user.save()
    return user, True


def extract_manager_identity(creators):
    manager_uid = None
    manager_email = None
    for c in creators:
        if not manager_uid:
            manager_uid = c.get("ManagerID")
        if not manager_email:
            manager_email = c.get("ManagerEmail")
        if manager_uid or manager_email:
            break
    return manager_uid, manager_email


# ------------------ Main Save Function ------------------
def save_manager_chunk(manager_data, month_code, chunk_size=10):
    report_month = get_reporting_month(month_code)
    manager_name = manager_data.get("Creator Network manager")
    print(f"\n🧑 Manager incoming: {manager_name}")

    creators = manager_data.get("creators", [])
    manager_uid, manager_email = extract_manager_identity(creators)

    # Create or update manager user
    user_m, _ = get_or_create_user_by_uid_or_username(
        uid=manager_uid,
        username=manager_name,
        role="MANAGER",
        name=manager_name,
        email=manager_email,
    )

    # Save Manager record
    manager, created = Manager.objects.update_or_create(
        user=user_m,
        report_month=report_month,
        defaults={
            "manager_uid": manager_uid,
            "eligible_creators": safe_int(manager_data.get("Eligible creators")),
            "estimated_bonus_contribution": parse_money(
                manager_data.get("Estimated bonus contribution")
            ),
            "diamonds": parse_diamonds(manager_data.get("Diamonds")),
            "M_0_5": safe_int(manager_data.get("M0.5")),
            "M1": safe_int(manager_data.get("M1")),
            "M2": safe_int(manager_data.get("M2")),
            "M1R": safe_int(manager_data.get("M1R")),
        },
    )

    # Process creators in chunks
    for i in range(0, len(creators), chunk_size):
        chunk = creators[i : i + chunk_size]
        with transaction.atomic():
            for c in chunk:
                creator_name = c.get("Creator")
                if not creator_name:
                    continue
                creator_display_name = c.get("CreatorName")
                creator_uid = c.get("CreatorID")
                creator_email = c.get("CreatorEmail")

                user_c, _ = get_or_create_user_by_uid_or_username(
                    uid=creator_uid,
                    username=creator_name,
                    name=creator_display_name,
                    role="CREATOR",
                    email=creator_email,
                )
                if not user_c:
                    print(f"❌ Skipping creator {creator_name} because UID is missing")
                    continue

                Creator.objects.update_or_create(
                    creator_uid=creator_uid,
                    report_month=report_month,
                    defaults={
                        "user": user_c,
                        "manager": manager,
                        "group_name": c.get("GroupName"),
                        "estimated_bonus_contribution": parse_money(
                            c.get("Estimated bonus contribution")
                        ),
                        "achieved_milestones": parse_milestones(
                            c.get("Achieved milestones")
                        ),
                        "diamonds": parse_diamonds(c.get("Diamonds")),
                        "valid_go_live_days": parse_days(c.get("Valid go LIVE days")),
                        "live_duration": parse_float(c.get("LIVE duration")),
                    },
                )

        print(f"✅ Saved creators {i+1} → {i+len(chunk)} for {manager_name}")


# ------------------ Run Script ------------------
if __name__ == "__main__":
    print("🚀 load_data.py started")

    current_month = timezone.now().strftime("%Y%m")
    # current_month = "202601"

    def on_manager_scraped(manager_data):
        save_manager_chunk(manager_data, current_month)

    scrape_dashboard(on_manager=on_manager_scraped)

    print("🏁 DONE")
