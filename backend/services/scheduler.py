import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import SessionLocal

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def sync_garmin_today() -> None:
    from backend.services.garmin import GarminSyncError, get_garmin_client, sync_date
    try:
        client = get_garmin_client()
        db = SessionLocal()
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            inserted_today = sync_date(client, today, db)
            inserted_yesterday = sync_date(client, yesterday, db)
            logger.info(
                "Garmin sync complete: %d new readings today, %d yesterday",
                inserted_today,
                inserted_yesterday,
            )
        finally:
            db.close()
    except GarminSyncError as e:
        logger.warning("Garmin sync skipped: %s", e)
    except Exception:
        logger.exception("Garmin sync failed unexpectedly")


def start_scheduler() -> None:
    scheduler.add_job(sync_garmin_today, "interval", hours=1, id="garmin_sync", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — Garmin sync every hour")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
