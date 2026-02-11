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

from scripts.load_data import scrape_dashboard, save_manager_chunk


def run():
    month = datetime.now().strftime("%Y%m")
    # month = "202601"
    print("🚀 Scraper started for month:", month)

    scrape_dashboard(on_manager=lambda m: save_manager_chunk(m, month))

    print("✅ Scraper finished")


if __name__ == "__main__":
    run()
