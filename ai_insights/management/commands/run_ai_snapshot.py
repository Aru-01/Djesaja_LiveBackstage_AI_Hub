from django.core.management.base import BaseCommand
from ai_insights.services import (
    build_ai_snapshot,
    run_ai_service,
    store_monthly_ai_response,
    store_daily_ai_response,
)
from ai_insights.services import auto_run_mode
from creators.models import Creator
from managers.models import Manager


class Command(BaseCommand):
    help = "Run AI snapshot (monthly or daily) and store results in DB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode",
            type=str,
            choices=["monthly", "daily"],
            help="Run mode: monthly or daily",
        )
        parser.add_argument(
            "--creator_limit",
            type=int,
            default=100,
            help="Limit number of creators for testing",
        )

    def handle(self, *args, **options):
        mode = options.get("mode")
        creator_limit = options.get("creator_limit")
        if not mode:
            mode, month_code = auto_run_mode()
        else:
            from ai_insights.services import get_month_code

            month_code = get_month_code(prev_month=(mode == "monthly"))

        print(f"Running AI snapshot: mode={mode}, month_code={month_code}")

        # Build snapshot
        snapshot = build_ai_snapshot(
            month_code, "month_start" if mode == "monthly" else "daily"
        )

        # Limit creators for testing
        if creator_limit and "creators" in snapshot:
            snapshot_creators = snapshot.get("creators") or snapshot.get(
                "previous_creators"
            )
            snapshot_creators = snapshot_creators[:creator_limit]
            if mode == "monthly":
                snapshot["previous_creators"] = snapshot_creators
            else:
                snapshot["creators"] = snapshot_creators

        # Run AI service
        response = run_ai_service(
            month_code, "month_start" if mode == "monthly" else "daily"
        )

        # Add admin messages manually if needed
        if "welcome_messages" in response and mode == "monthly":
            response["welcome_messages"]["messages"].append(
                {
                    "role": "admin",
                    "id": "admin",
                    "type": "month_start_overview",
                    "message": "Admin overview message for testing",
                }
            )

        # Store in DB
        if mode == "monthly":
            store_monthly_ai_response(response, month_code)
        else:
            store_daily_ai_response(response, month_code)

        print(f"AI snapshot {mode} run completed successfully.")
