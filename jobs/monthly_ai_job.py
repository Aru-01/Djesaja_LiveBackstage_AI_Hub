import os
import django
from datetime import date, timedelta
import os, sys

# --- add project root to PYTHONPATH ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# --- tell Django where settings are ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Djesaja_LiveBackstage.settings")

import django

django.setup()

from ai_insights.ai_requests import run_chunked_ai


def run():
    first_day_this_month = date.today().replace(day=1)
    prev_month = first_day_this_month - timedelta(days=1)
    month_code = prev_month.strftime("%Y%m")
    print(f"📊 Monthly AI job started for month {month_code}")
    run_chunked_ai(mode="month_start", month_code=month_code)
    print("✅ Monthly AI job done")


if __name__ == "__main__":
    run()
