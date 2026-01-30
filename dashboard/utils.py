# dashboard/utils.py
from django.db.models import Sum, Count, F, Window, Q
from django.db.models.functions import RowNumber
from django.contrib.auth import get_user_model
from django.utils import timezone
from creators.models import Creator
from managers.models import Manager
from api.models import ReportingMonth
from ai_insights.models import AITarget, AIManagerTarget
import calendar


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


def get_prev_n_months_codes(report_month, n=3):
    """
    Return last n months codes (YYYYMM) from report_month, always n items
    Missing months not in DB still included as YYYYMM
    """
    months = []
    month_code_int = int(report_month.code)  # 🔥 convert string to int
    year = month_code_int // 100
    month = month_code_int % 100

    for _ in range(n):
        months.append(f"{year}{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months


def month_code_to_name(month_code):
    """
    YYYYMM -> Month name (January, February...)
    """
    year = int(month_code[:4])
    month = int(month_code[4:])
    return calendar.month_name[month]


def build_last_3_months_stats(stats_lookup, entity_id, last_months_codes):
    data = {}
    for code in last_months_codes:
        month_name = month_code_to_name(code)
        data[month_name] = {
            "diamonds": stats_lookup.get(entity_id, {})
            .get(code, {})
            .get("diamonds", 0),
            "hours": stats_lookup.get(entity_id, {}).get(code, {}).get("hours", 0),
        }
    return data


User = get_user_model()


def get_managers_data(report_month, manager_id=None):
    prev_month = get_prev_month_of(report_month)
    last_months_codes = get_prev_n_months_codes(report_month, n=3)

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

    manager_ids = [m.id for m in qs]

    stats_qs = (
        Creator.objects.filter(
            manager_id__in=manager_ids,
            report_month__code__in=last_months_codes,
        )
        .values("manager_id", "report_month__code")
        .annotate(
            total_diamonds=Sum("diamonds"),
            total_hours=Sum("live_duration"),
        )
    )
    stats_lookup = {}

    for row in stats_qs:
        stats_lookup.setdefault(row["manager_id"], {})[row["report_month__code"]] = {
            "diamonds": row["total_diamonds"] or 0,
            "hours": row["total_hours"] or 0,
        }

    # 🔹 prev_month targets for all managers
    targets_qs = AIManagerTarget.objects.filter(
        user_id__in=[m.user.id for m in qs], report_month=prev_month
    )
    targets_lookup = {t.user_id: t.team_target_diamonds or 0 for t in targets_qs}

    manager_list = []
    for m in qs:
        last_3_months = build_last_3_months_stats(stats_lookup, m.id, last_months_codes)

        target_diamonds = targets_lookup.get(m.user.id, 0)
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
                "last_3_months": last_3_months,
            }
        )

    if manager_id:
        manager_list = [m for m in manager_list if m["id"] == int(manager_id)]

    return manager_list


def get_creators_data(report_month, creator_id=None, manager_id=None):
    prev_month = get_prev_month_of(report_month)
    last_months_codes = get_prev_n_months_codes(report_month, n=3)

    qs = Creator.objects.filter(
        report_month=report_month, manager_id=manager_id
    ).select_related("user", "manager__user")

    creator_ids = [c.user.id for c in qs]
    stats_qs = (
        Creator.objects.filter(
            user_id__in=creator_ids,
            report_month__code__in=last_months_codes,
        )
        .values("user_id", "report_month__code")
        .annotate(
            total_diamonds=Sum("diamonds"),
            total_hours=Sum("live_duration"),
        )
    )

    stats_lookup = {}
    for row in stats_qs:
        stats_lookup.setdefault(row["user_id"], {})[row["report_month__code"]] = {
            "diamonds": row["total_diamonds"] or 0,
            "hours": row["total_hours"] or 0,
        }

    targets_qs = AITarget.objects.filter(
        user_id__in=creator_ids, report_month=prev_month
    )
    targets_lookup = {t.user_id: t.target_diamonds or 0 for t in targets_qs}

    # 🔹 ranking
    qs = qs.annotate(
        rank=Window(
            expression=RowNumber(),
            partition_by=[F("manager_id")],
            order_by=F("diamonds").desc(),
        )
    ).order_by("-diamonds")

    creator_list = []
    for c in qs:
        last_3_months = build_last_3_months_stats(
            stats_lookup, c.user.id, last_months_codes
        )
        target_diamonds = targets_lookup.get(c.user.id, 0)

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
                "last_3_months": last_3_months,
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
