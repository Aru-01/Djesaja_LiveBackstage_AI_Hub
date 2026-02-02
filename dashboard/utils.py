from django.db.models import Sum, Count, F, Window, Q, Subquery, OuterRef
from django.db.models.functions import RowNumber
from django.contrib.auth import get_user_model
from django.utils import timezone
from creators.models import Creator
from managers.models import Manager
from ai_insights.models import AITarget, AIManagerTarget, AIDailySummary
from dashboard.helpers import (
    get_prev_month_of,
    get_prev_n_months_codes,
    build_last_3_months_stats,
)


User = get_user_model()


def get_managers_data(report_month, manager_id=None, search=None):
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
    if search:
        qs = qs.filter(user__username__icontains=search)

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

    # prev_month targets for all managers
    targets_qs = AIManagerTarget.objects.filter(
        user_id__in=[m.user.id for m in qs], report_month=prev_month
    )
    targets_lookup = {t.user_id: t.team_target_diamonds or 0 for t in targets_qs}

    latest_priority = Subquery(
        AIDailySummary.objects.filter(user=OuterRef("user"))
        .order_by("-updated_at")
        .values("priority")[:1]
    )
    all_creators = (
        Creator.objects.filter(report_month=report_month, manager_id__in=manager_ids)
        .select_related("user")
        .annotate(latest_priority=latest_priority)
    )

    # Annotate alert count per manager
    alert_counts_qs = all_creators.values("manager_id").annotate(
        at_risk=Count(
            "id",
            filter=Q(latest_priority__iexact="high"),
            distinct=True,
        ),
        excellent=Count(
            "id",
            filter=Q(latest_priority__isnull=True),
            distinct=True,
        ),
    )

    alerts_lookup = {
        row["manager_id"]: {"at_risk": row["at_risk"], "excellent": row["excellent"]}
        for row in alert_counts_qs
    }

    manager_list = []
    for m in qs:
        last_3_months = build_last_3_months_stats(stats_lookup, m.id, last_months_codes)

        target_diamonds = targets_lookup.get(m.user.id, 0)
        #  alert counts
        alerts = alerts_lookup.get(m.id, {"at_risk": 0, "excellent": 0})
        manager_list.append(
            {
                "id": m.id,
                "username": m.user.username,
                "profile_image": (
                    m.user.profile_image.url if m.user.profile_image else None
                ),
                "my_creators": m.my_creators or 0,
                "rank": m.rank,
                "total_coin": m.total_coin or 0,
                "total_hour": m.total_hour or 0,
                "total_diamond": m.total_diamond or 0,
                "target_diamonds": target_diamonds,
                "last_3_months": last_3_months,
                "at_risk": alerts["at_risk"],
                "excellent": alerts["excellent"],
            }
        )

    if manager_id:
        manager_list = [m for m in manager_list if m["id"] == int(manager_id)]

    return manager_list


def get_creators_data(report_month, creator_id=None, manager_id=None, search=None):
    prev_month = get_prev_month_of(report_month)
    last_months_codes = get_prev_n_months_codes(report_month, n=3)

    qs = Creator.objects.filter(report_month=report_month).select_related(
        "user", "manager__user"
    )

    if manager_id:
        qs = qs.filter(manager_id=manager_id)

    if search:
        qs = qs.filter(user__username__icontains=search)

    creator_ids = [c.user.id for c in qs]

    stats_qs = (
        Creator.objects.filter(
            user_id__in=creator_ids, report_month__code__in=last_months_codes
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

    qs = qs.annotate(
        rank=Window(
            expression=RowNumber(),
            partition_by=[F("manager_id")],
            order_by=F("diamonds").desc(),
        )
    ).order_by("manager_id", "-diamonds")

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
                "profile_image": (
                    c.user.profile_image.url if c.user.profile_image else None
                ),
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

    prev_month = get_prev_month_of(report_month)

    admin_target = (
        AIManagerTarget.objects.filter(report_month=prev_month)
        .aggregate(total_target=Sum("team_target_diamonds"))
        .get("total_target")
        or 0
    )
    last_months_codes = get_prev_n_months_codes(report_month, n=3)

    stats_qs = (
        Creator.objects.filter(report_month__code__in=last_months_codes)
        .values("report_month__code")
        .annotate(
            total_diamonds=Sum("diamonds"),
            total_hours=Sum("live_duration"),
        )
    )
    stats_lookup = {}

    for row in stats_qs:
        stats_lookup[row["report_month__code"]] = {
            "diamonds": row["total_diamonds"] or 0,
            "hours": row["total_hours"] or 0,
        }
    admin_last_3_months = build_last_3_months_stats(
        {"admin": stats_lookup}, "admin", last_months_codes
    )

    return {
        "total_creators": agg["total_creators"] or 0,
        "total_managers": total_managers,
        "scrape_today": scrape_today,
        "total_diamond_achieve": agg["total_diamond_achieve"] or 0,
        "total_coin": agg["total_coin"] or 0,
        "total_hour": agg["total_hour"] or 0,
        "target_diamonds": admin_target,
        "last_3_months": admin_last_3_months,
    }
