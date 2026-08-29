import asyncio
import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.webhook import router as webhook_router
from app.db.session import init_db
from app.scheduler.worker import run_worker
from app.settings import get_settings

logging.basicConfig(
    level=get_settings().log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
app = FastAPI(title="CLEX Pharma", version="0.1.0")
app.include_router(health_router)
app.include_router(webhook_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


if __name__ == "__main__":
    settings = get_settings()
    if settings.process_role == "worker":
        asyncio.run(run_worker())
    else:
        import uvicorn

        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
