from datetime import datetime
import os
from playwright.sync_api import sync_playwright, TimeoutError
import json, time, random

today = datetime.today()
month_str = today.strftime("%Y%m")
# month_str = "202601"

DASHBOARD_URL = (
    f"https://live-backstage.tiktok.com/portal/revenue/task"
    f"?Month={month_str}"
    f"&SettleJobID=7588868461859340299"
    f"&SettleSubJobID=7588868461859373067"
    f"&TaskID=7451459313831955206"
    f"&subViewTab=EligibleAnchor"
    f"&viewTab=by_manager"
)

# OUTPUT_FILE = "test.json"
OUTPUT_FILE = None
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")


# ---------------- UTILITIES ----------------


def human_delay(a=800, b=1500):
    time.sleep(random.randint(a, b) / 1000)


def safe_text(locator, timeout=4000):
    try:
        return locator.inner_text(timeout=timeout).strip()
    except:
        return ""


def save_progress(data):
    if not OUTPUT_FILE:
        return
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def close_modal(page):
    try:
        btn = page.locator(
            'button.semi-sidesheet-close, button[aria-label="Close"]'
        ).first
        if btn.count():
            btn.click()
            page.wait_for_timeout(500)
        else:
            page.keyboard.press("Escape")
    except:
        page.keyboard.press("Escape")


def normalize_creator(data):
    host_info = data.get("HostBaseInfo", {})
    agent_info = host_info.get("AgentInfo", {})

    return {
        "CreatorID": host_info.get("CreatorID") or data.get("CreatorID", ""),
        "user_id": host_info.get("user_id") or data.get("user_id", ""),
        "nickname": host_info.get("nickname") or data.get("nickname", ""),
        "display_id": host_info.get("display_id") or data.get("display_id", ""),
        "AgentID": agent_info.get("AgentID", ""),
        "AgentName": agent_info.get("AgentName", ""),
        "GroupName": agent_info.get("GroupName", ""),
    }


# ---------------- MAIN SCRAPER ----------------


def scrape_dashboard(on_manager=None):
    global scrape_succeeded
    print("🟢 SCRAPER STARTED → load_data.py called me")

    MAX_RETRIES = 10
    retry = 0

    while retry < MAX_RETRIES:
        final_data = []
        scrape_succeeded = False
        manager_page = 1

        with sync_playwright() as p:
            # browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            browser = p.chromium.launch(headless=True, args=["--start-maximized"])

            ctx = browser.new_context(
                storage_state=STATE_FILE,
                viewport={"width": 1920, "height": 1080},
            )

            page = ctx.new_page()
            page.goto(DASHBOARD_URL)
            page.wait_for_selector('[role="row"][aria-rowindex]')
            time.sleep(2)

            while True:
                print(f"\n📄 Manager page {manager_page}")

                rows = page.locator('[role="row"][aria-rowindex]')
                row_count = rows.count()

                for i in range(row_count):
                    row = rows.nth(i)
                    manager_name = safe_text(row.locator('[aria-colindex="1"]'))

                    if (
                        not manager_name
                        or manager_name.lower() == "creator network manager"
                    ):
                        continue

                    print("➡️", manager_name)

                    eligible = safe_text(row.locator('[aria-colindex="2"]'))

                    manager = {
                        "Creator Network manager": manager_name,
                        "Eligible creators": eligible,
                        "Estimated bonus contribution": safe_text(
                            row.locator('[aria-colindex="3"]')
                        ),
                        "Diamonds": safe_text(row.locator('[aria-colindex="4"]')),
                        "M0.5": safe_text(row.locator('[aria-colindex="5"]')),
                        "M1": safe_text(row.locator('[aria-colindex="6"]')),
                        "M2": safe_text(row.locator('[aria-colindex="7"]')),
                        "M1R": safe_text(row.locator('[aria-colindex="8"]')),
                        "creators": [],
                    }

                    scrape_succeeded = True
                    if eligible == "0":
                        # final_data.append(manager)
                        if on_manager:
                            on_manager(manager)
                        else:
                            final_data.append(manager)

                        save_progress(final_data)
                        continue

                    btn = row.locator('[aria-colindex="2"] button')
                    if not btn.count():
                        # final_data.append(manager)
                        if on_manager:
                            on_manager(manager)
                        else:
                            final_data.append(manager)
                        save_progress(final_data)
                        continue

                    btn.click()
                    human_delay(1200, 1800)

                    try:
                        page.wait_for_selector(
                            '[role="dialog"], .semi-sidesheet, .semi-modal',
                            timeout=5000,
                        )
                    except:
                        # final_data.append(manager)
                        if on_manager:
                            on_manager(manager)
                        else:
                            final_data.append(manager)
                        save_progress(final_data)
                        continue

                    creator_counter = 0

                    while True:
                        page.wait_for_timeout(800)

                        crows = page.locator(
                            '[role="dialog"] [role="row"][aria-rowindex],'
                            ' .semi-sidesheet [role="row"][aria-rowindex]'
                        )

                        for j in range(crows.count()):
                            crow = crows.nth(j)
                            creator_name = safe_text(
                                crow.locator('[aria-colindex="1"]')
                            )

                            if not creator_name or creator_name.lower() == "creator":
                                continue

                            crow.scroll_into_view_if_needed()
                            page.mouse.move(0, 0)
                            page.wait_for_timeout(150)

                            creator_xhr = {}

                            try:
                                with page.expect_response(
                                    lambda r: "anchor_profile" in r.url,
                                    timeout=5000,
                                ) as resp:
                                    crow.locator("span.avatarContainer-yJA0K2").hover(
                                        force=True
                                    )

                                response = resp.value
                                data = response.json()
                                creator_xhr = normalize_creator(data)

                                print(
                                    f"🎯 XHR OK: {creator_xhr.get('AgentName')} | "
                                    f"{creator_xhr.get('CreatorID')}"
                                )

                            except TimeoutError:
                                print("⚠️ XHR timeout:", creator_name)

                            creator_data = {
                                "CreatorID": creator_xhr.get("CreatorID", "N/A"),
                                "ManagerEmail": creator_xhr.get("AgentName", "N/A"),
                                "Creator": creator_name,
                                "Estimated bonus contribution": safe_text(
                                    crow.locator('[aria-colindex="2"]')
                                ),
                                "Achieved milestones": safe_text(
                                    crow.locator('[aria-colindex="3"]')
                                ),
                                "Diamonds": safe_text(
                                    crow.locator('[aria-colindex="4"]')
                                ),
                                "Valid go LIVE days": safe_text(
                                    crow.locator('[aria-colindex="5"]')
                                ),
                                "LIVE duration": safe_text(
                                    crow.locator('[aria-colindex="6"]')
                                ),
                                "CreatorName": creator_xhr.get("nickname", ""),
                                "ManagerID": creator_xhr.get("AgentID", ""),
                                "GroupName": creator_xhr.get("GroupName", ""),
                            }

                            manager["creators"].append(creator_data)
                            save_progress(final_data)

                            creator_counter += 1
                            if creator_counter % 50 == 0:
                                print("⏸ creator break 2s")
                                time.sleep(2)

                        next_btn = page.locator(
                            '[role="dialog"] .semi-page-next,'
                            " .semi-sidesheet .semi-page-next"
                        ).first

                        if (
                            not next_btn.count()
                            or next_btn.get_attribute("aria-disabled") == "true"
                        ):
                            break

                        next_btn.click()
                        human_delay(1200, 1800)

                    close_modal(page)
                    # final_data.append(manager)
                    if on_manager:
                        on_manager(manager)
                    else:
                        final_data.append(manager)
                    save_progress(final_data)
                    human_delay(800, 1200)

                next_page = page.locator("#task-v2-page .semi-page-next").first
                if (
                    not next_page.count()
                    or next_page.get_attribute("aria-disabled") == "true"
                ):
                    break

                next_page.click()
                manager_page += 1
                human_delay(1500, 2200)

            browser.close()

        print(f"\n✅ DONE. Total managers: {len(final_data)}")

        if scrape_succeeded:
            break
        else:
            retry += 1
            print(f"⚠️ Retry {retry}/{MAX_RETRIES}")
            time.sleep(5)

    if len(final_data) == 0:
        # print("❌ Scraper failed after max retries.")
        return []
    else:
        print("✅ Scraper completed successfully.")
        return final_data


if __name__ == "__main__":
    scrape_dashboard()
