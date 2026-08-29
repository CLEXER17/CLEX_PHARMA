import asyncio
import logging

from app.db.session import init_db

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    init_db()
    while True:
        logger.info("worker heartbeat; discovery adapters are ready")
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run_worker())
