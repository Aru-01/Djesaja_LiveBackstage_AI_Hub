import os
import django
from datetime import datetime
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
    today = datetime.today()
    print(f"🤖 Daily AI job started ")
    mode = "daily"
    month_code = today.strftime("%Y%m")
    print(month_code)
    run_chunked_ai(month_code, mode)
    print("✅ Daily AI job done")


if __name__ == "__main__":
    run()
