import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRAPER_PATH = os.path.join(BASE_DIR, "scrape_job.py")
DAILY_AI_PATH = os.path.join(BASE_DIR, "daily_ai_job.py")
LOCK_FILE = "/tmp/scraper_daily.lock"


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
    # Use flock to prevent overlap
    try:
        # Try to acquire lock
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("🚫 Scraper already running. Exiting...")
        return

    try:
        print("🚀 Running scraper...")
        success = run_script(SCRAPER_PATH)
        if success:
            print("🤖 Running daily AI job...")
            run_script(DAILY_AI_PATH)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


if __name__ == "__main__":
    main()
