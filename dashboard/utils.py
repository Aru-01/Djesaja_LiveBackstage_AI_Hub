# dashboard/utils.py
from django.db.models import Sum, Count, F, Window, Q
from django.db.models.functions import RowNumber
from django.contrib.auth import get_user_model
from django.utils import timezone
from creators.models import Creator
from managers.models import Manager
from api.models import ReportingMonth


def get_report_month(month_code=None):
    if month_code:
        return ReportingMonth.objects.get(code=month_code)
    return ReportingMonth.objects.latest("id")


User = get_user_model()


def get_managers_data(report_month, manager_id=None):
    """
    Optimized: avoids N+1 queries using annotate and prefetch_related
    """

    qs = Manager.objects.filter(report_month=report_month).select_related("user")
    if manager_id:
        qs = qs.filter(id=manager_id)

    # Annotate rank
    qs = qs.annotate(
        manager_position=Window(
            expression=RowNumber(), order_by=F("eligible_creators").desc()
        )
    )

    # Annotate creator aggregates
    qs = qs.annotate(
        my_creators=Count(
            "creators", filter=Q(creators__report_month=report_month), distinct=True
        ),
        total_coin=Sum(
            "creators__estimated_bonus_contribution",
            filter=Q(creators__report_month=report_month),
        ),
        total_hour=Sum(
            "creators__live_duration", filter=Q(creators__report_month=report_month)
        ),
        total_diamond=Sum(
            "creators__diamonds", filter=Q(creators__report_month=report_month)
        ),
    )

    manager_list = []
    for m in qs:
        manager_list.append(
            {
                "id": m.id,
                "username": m.user.username,
                "my_creators": m.my_creators or 0,
                "manager_position": m.manager_position,
                "total_coin": m.total_coin or 0,
                "total_hour": m.total_hour or 0,
                "total_diamond": m.total_diamond or 0,
            }
        )

    return manager_list


def get_creators_data(report_month, creator_id=None):
    """
    Returns list of creators.
    If creator_id provided, returns single creator in a list.
    """
    qs = Creator.objects.select_related("user", "manager__user").filter(
        report_month=report_month
    )
    if creator_id:
        qs = qs.filter(id=creator_id)

    # Annotate rank
    qs = qs.annotate(
        rank=Window(
            expression=RowNumber(), order_by=F("estimated_bonus_contribution").desc()
        )
    )

    creator_list = []
    for c in qs:
        creator_list.append(
            {
                "id": c.id,
                "username": c.user.username,
                "manager_id": c.manager.id,
                "manager_username": c.manager.user.username,
                "total_coin": c.estimated_bonus_contribution,
                "total_hour": c.live_duration,
                "total_diamond": c.diamonds,
                "my_rank": c.rank,
            }
        )
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
