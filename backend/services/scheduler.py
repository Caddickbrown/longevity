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


def generate_research_digest() -> None:
    """Fetch latest longevity research and synthesise a digest via Claude."""
    from backend.config import settings
    from backend.models import Intervention, ResearchDigest
    from backend.services.research_fetcher import FetchError, fetch_research
    from backend.services.research_synthesiser import SynthesisError, synthesise
    from sqlalchemy import select

    if not settings.anthropic_api_key:
        logger.info("Research digest skipped — ANTHROPIC_API_KEY not set")
        return

    db = SessionLocal()
    try:
        protocols = db.execute(select(Intervention.name)).scalars().all()
        articles = fetch_research()
        digest_data = synthesise(articles, list(protocols))
        db.add(ResearchDigest(**digest_data))
        db.commit()
        logger.info("Research digest generated — %d interventions mentioned", len(digest_data["interventions_mentioned"]))
    except (FetchError, SynthesisError) as e:
        logger.warning("Research digest failed: %s", e)
    except Exception:
        logger.exception("Research digest failed unexpectedly")
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(sync_health_data, "interval", hours=1, id="health_sync", replace_existing=True)
    scheduler.add_job(generate_research_digest, "cron", day_of_week="sun", hour=6, id="research_digest", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — health sync hourly, research digest weekly (Sun 06:00)")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
