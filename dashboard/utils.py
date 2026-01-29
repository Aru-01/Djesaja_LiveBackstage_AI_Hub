# dashboard/utils.py
from django.db.models import Sum, Count, F, Window, Q
from django.db.models.functions import RowNumber
from django.contrib.auth import get_user_model
from django.utils import timezone
from creators.models import Creator
from managers.models import Manager
from api.models import ReportingMonth
from ai_insights.models import AITarget, AIManagerTarget


def get_prev_month_of(report_month):
    """
    Return previous ReportingMonth object before the given report_month
    If none exists, return None
    """
    prev_month = (
        ReportingMonth.objects.filter(code__lt=report_month.code)
        .order_by("-code")
        .first()
    )
    return prev_month


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
    prev_month = get_prev_month_of(report_month)

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

    manager_list = []
    for m in qs:
        # default target
        target_diamonds = 0

        if prev_month:
            target = AIManagerTarget.objects.filter(
                user=m.user, report_month=prev_month
            ).first()
            if target:
                target_diamonds = target.team_target_diamonds or 0

        manager_list.append(
            {
                "id": m.id,
                "username": m.user.username,
                "my_creators": m.my_creators or 0,
                "rank": m.rank,
                "total_coin": m.total_coin or 0,
                "total_hour": m.total_hour or 0,
                "total_diamond": m.total_diamond or 0,
                "target_diamonds": target_diamonds,
            }
        )

    if manager_id:
        manager_list = [m for m in manager_list if m["id"] == int(manager_id)]

    return manager_list


def get_creators_data(report_month, creator_id=None, manager_id=None):
    prev_month = get_prev_month_of(report_month)

    qs = Creator.objects.filter(
        report_month=report_month, manager_id=manager_id  # 🔥 manager wise filter
    ).select_related("user", "manager__user")

    # 🔥 manager-wise ranking
    qs = qs.annotate(
        rank=Window(
            expression=RowNumber(),
            partition_by=[F("manager_id")],
            order_by=F("diamonds").desc(),
        )
    ).order_by("-diamonds")

    creator_list = []

    for c in qs:
        target_diamonds = 0
        if prev_month:
            target = AITarget.objects.filter(
                user=c.user, report_month=prev_month
            ).first()
            if target:
                target_diamonds = target.target_diamonds or 0

        creator_list.append(
            {
                "id": c.id,
                "username": c.user.username,
                "manager_id": c.manager.id if c.manager else None,
                "manager_username": c.manager.user.username if c.manager else None,
                "total_coin": c.estimated_bonus_contribution,
                "total_hour": c.live_duration,
                "total_diamond": c.diamonds,
                "rank": c.rank,
                "target_diamonds": target_diamonds,
            }
        )

    if creator_id:
        creator_list = [c for c in creator_list if c["id"] == int(creator_id)]

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
