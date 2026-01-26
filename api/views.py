# from django.db.models import Sum, Count
# from django.utils import timezone
# from creators.models import Creator
# from managers.models import Manager

# # Create your views here.


# def admin_dashboard_data(report_month):
#     today = timezone.now().date()

#     total_creators = Creator.objects.filter(report_month=report_month).count()
#     total_managers = Manager.objects.filter(report_month=report_month).count()

#     scrape_today = Creator.objects.filter(
#         report_month=report_month, created_at__date=today
#     ).count()

#     total_diamond_achieve = (
#         Creator.objects.filter(report_month=report_month).aggregate(
#             total=Sum("diamonds")
#         )["total"]
#         or 0
#     )

#     total_coin = (
#         Creator.objects.filter(report_month=report_month).aggregate(
#             total=Sum("estimated_bonus_contribution")
#         )["total"]
#         or 0
#     )

#     total_hour = (
#         Creator.objects.filter(report_month=report_month).aggregate(
#             total=Sum("live_duration")
#         )["total"]
#         or 0
#     )

#     return {
#         "total_creators": total_creators,
#         "total_managers": total_managers,
#         "scrape_today": scrape_today,
#         "total_diamond_achieve": total_diamond_achieve,
#         "total_coin": total_coin,
#         "total_hour": total_hour,
#     }


# def manager_dashboard_data(manager, report_month):
#     creators_qs = Creator.objects.filter(manager=manager, report_month=report_month)

#     my_creators = creators_qs.count()

#     # Manager position could be defined by e.g., eligible creators rank
#     managers = Manager.objects.filter(report_month=report_month).order_by(
#         "-eligible_creators"
#     )
#     position = list(managers).index(manager) + 1  # 1-based index

#     total_coin = (
#         creators_qs.aggregate(total=Sum("estimated_bonus_contribution"))["total"] or 0
#     )
#     total_hour = creators_qs.aggregate(total=Sum("live_duration"))["total"] or 0
#     total_diamond = creators_qs.aggregate(total=Sum("diamonds"))["total"] or 0

#     return {
#         "my_creators": my_creators,
#         "manager_position": position,
#         "total_coin": total_coin,
#         "total_hour": total_hour,
#         "total_diamond": total_diamond,
#     }


# def creator_dashboard_data(creator, report_month):
#     creators_qs = Creator.objects.filter(report_month=report_month).order_by(
#         "-estimated_bonus_contribution"
#     )

#     # Rank calculation
#     rank = list(creators_qs).index(creator) + 1  # 1-based rank

#     total_coin = creator.estimated_bonus_contribution
#     total_hour = creator.live_duration
#     total_diamond = creator.diamonds

#     return {
#         "my_rank": rank,
#         "total_coin": total_coin,
#         "total_hour": total_hour,
#         "total_diamond": total_diamond,
#     }
