from django.utils import timezone
from api.models import ReportingMonth
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

        hours = stats_lookup.get(entity_id, {}).get(code, {}).get("hours", 0)

        data[month_name] = {
            "diamonds": (
                stats_lookup.get(entity_id, {}).get(code, {}).get("diamonds", 0)
            ),
            "hours": round(hours, 2),
        }
    return data
