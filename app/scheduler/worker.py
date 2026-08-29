import asyncio
import logging

from app.db.session import init_db
from app.ingestion.orchestrator import run_ingestion_cycle
from app.settings import get_settings

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    init_db()
    while True:
        logger.info("starting ingestion cycle")
        try:
            totals = await run_ingestion_cycle()
            logger.info("ingestion cycle complete: %s", totals)
        except Exception:
            logger.exception("ingestion cycle failed")
        await asyncio.sleep(settings.crawl_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run_worker())
