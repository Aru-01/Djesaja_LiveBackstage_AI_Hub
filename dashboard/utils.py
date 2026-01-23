# dashboard/utils.py
from django.db.models import Sum, Count, F, Window, Q
from django.db.models.functions import RowNumber
from django.contrib.auth import get_user_model
from django.utils import timezone
from creators.models import Creator
from managers.models import Manager
from api.models import ReportingMonth


def get_report_month(month_code=None):
    """
    Priority:
    1. If month_code provided → use it
    2. Else → use current month YYYYMM
    """

    if not month_code:
        now = timezone.now()
        month_code = f"{now.year}{now.month:02d}"

    return ReportingMonth.objects.get(code=month_code)


User = get_user_model()


def get_managers_data(report_month, manager_id=None):
    """
    Returns list of managers with correct rank based on total diamonds of their creators.
    Aggregates total_hour, total_coin, total_diamond, my_creators.
    """

    qs = (
        Manager.objects.filter(report_month=report_month)
        .select_related("user")
        .annotate(
            my_creators=Count(
                "creators", filter=Q(creators__report_month=report_month), distinct=True
            ),
            total_coin=Sum(
                "creators__estimated_bonus_contribution",
                filter=Q(creators__report_month=report_month),
            ),
            total_hour=Sum(
                "creators__live_duration",
                filter=Q(creators__report_month=report_month),
            ),
            total_diamond=Sum(
                "creators__diamonds",
                filter=Q(creators__report_month=report_month),
            ),
        )
        .annotate(
            rank=Window(expression=RowNumber(), order_by=F("total_diamond").desc())
        )
        .order_by("-total_diamond")
    )

    manager_list = [
        {
            "id": m.id,
            "username": m.user.username,
            "my_creators": m.my_creators or 0,
            "rank": m.rank,
            "total_coin": m.total_coin or 0,
            "total_hour": m.total_hour or 0,
            "total_diamond": m.total_diamond or 0,
        }
        for m in qs
    ]

    if manager_id:
        manager_list = [m for m in manager_list if m["id"] == int(manager_id)]

    return manager_list


def get_creators_data(report_month, creator_id=None, manager_id=None):
    """
    Returns list of creators with correct global/month rank.
    - creator_id: filter for a single creator (optional)
    - manager_id: filter for creators under a specific manager (optional)
    """

    qs = (
        Creator.objects.filter(report_month=report_month)
        .select_related("user", "manager__user")
        .order_by("-diamonds")
        .annotate(rank=Window(expression=RowNumber(), order_by=F("diamonds").desc()))
    )

    creator_list = [
        {
            "id": c.id,
            "username": c.user.username,
            "manager_id": c.manager.id,
            "manager_username": c.manager.user.username,
            "total_coin": c.estimated_bonus_contribution,
            "total_hour": c.live_duration,
            "total_diamond": c.diamonds,
            "rank": c.rank,
        }
        for c in qs
    ]

    if creator_id:
        creator_list = [c for c in creator_list if c["id"] == int(creator_id)]

    if manager_id:
        creator_list = [c for c in creator_list if c["manager_id"] == int(manager_id)]

    return creator_list


def admin_dashboard_data(report_month):
    today = timezone.now().date()
    qs = Creator.objects.filter(report_month=report_month)

    agg = qs.aggregate(
        total_creators=Count("id"),
        total_diamond_achieve=Sum("diamonds"),
        total_coin=Sum("estimated_bonus_contribution"),
        total_hour=Sum("live_duration"),
    )
    scrape_today = qs.filter(created_at__date=today).count()
    total_managers = Manager.objects.filter(report_month=report_month).count()

    return {
        "total_creators": agg["total_creators"] or 0,
        "total_managers": total_managers,
        "scrape_today": scrape_today,
        "total_diamond_achieve": agg["total_diamond_achieve"] or 0,
        "total_coin": agg["total_coin"] or 0,
        "total_hour": agg["total_hour"] or 0,
    }
