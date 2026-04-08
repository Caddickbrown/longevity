import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import SessionLocal

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def sync_health_data() -> None:
    """Sync from health-at-home API (primary), Garmin Connect (fallback for HRV/VO2)."""
    from backend.services.health_bridge import HealthBridgeError, sync as bridge_sync
    from backend.services.garmin import GarminSyncError, get_garmin_client, sync_date

    db = SessionLocal()
    try:
        # Primary: health-at-home API (Apple Health data)
        try:
            inserted = bridge_sync(days=2, db_session=db)
            logger.info("health-at-home sync: %d new readings", inserted)
        except HealthBridgeError as e:
            logger.warning("health-at-home sync skipped: %s", e)

        # Fallback: Garmin Connect for HRV and VO2 max (not in Apple Health)
        try:
            client = get_garmin_client()
            today = date.today()
            yesterday = today - timedelta(days=1)
            inserted_garmin = sync_date(client, today, db) + sync_date(client, yesterday, db)
            if inserted_garmin:
                logger.info("Garmin sync: %d new readings (HRV/VO2)", inserted_garmin)
        except GarminSyncError as e:
            logger.debug("Garmin sync skipped (expected if no credentials): %s", e)
        except Exception:
            logger.exception("Garmin sync failed unexpectedly")

    except Exception:
        logger.exception("Health data sync failed unexpectedly")
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(sync_health_data, "interval", hours=1, id="health_sync", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — health sync every hour")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
