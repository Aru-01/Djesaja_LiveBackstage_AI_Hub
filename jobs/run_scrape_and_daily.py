import subprocess
import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRAPER_PATH = os.path.join(BASE_DIR, "scrape_job.py")
DAILY_AI_PATH = os.path.join(BASE_DIR, "daily_ai_job.py")
MONTHLY_JOB_PATH = os.path.join(BASE_DIR, "monthly_ai_job.py")


def run_script(path):
    """Run a Python script and return True if success, False if fail"""
    result = subprocess.run([sys.executable, path], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("❌ Error running:", path)
        print(result.stderr)
        return False
    return True


def main():
    print("🚀 Running scraper...")
    success = run_script(SCRAPER_PATH)

    if success:
        today = datetime.now()

        if today.day == 1:
            print("📅 Running monthly job...")
            run_script(MONTHLY_JOB_PATH)

        print("🤖 Running daily AI job...")
        run_script(DAILY_AI_PATH)


if __name__ == "__main__":
    main()
