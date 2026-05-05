from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import legs as legs_router
from .api import snapshot as snapshot_router
from .api import spreads as spreads_router
from .config import get_settings
from .db import SessionLocal
from .moomoo_client import MoomooClient
from .snapshotter import run_snapshot

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def _scheduled_snapshot(client: MoomooClient) -> None:
    db = SessionLocal()
    try:
        run_snapshot(db, client)
    except Exception:
        logger.exception("scheduled snapshot failed")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = MoomooClient(
        host=settings.moomoo_host,
        port=settings.moomoo_port,
        trade_pwd=settings.moomoo_trade_pwd,
        security_firm=settings.moomoo_security_firm,
        trd_market=settings.moomoo_trd_market,
    )
    app.state.moomoo_client = client

    scheduler = AsyncIOScheduler(timezone=settings.snapshot_tz)
    parts = settings.snapshot_cron.split()
    if len(parts) != 5:
        raise ValueError(f"SNAPSHOT_CRON must be 5 fields, got: {settings.snapshot_cron!r}")
    minute, hour, day, month, day_of_week = parts
    scheduler.add_job(
        _scheduled_snapshot,
        CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone=settings.snapshot_tz,
        ),
        args=[client],
        id="snapshot",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("scheduler started: cron=%r tz=%s", settings.snapshot_cron, settings.snapshot_tz)
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="credit-spread API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spreads_router.router)
app.include_router(legs_router.router)
app.include_router(snapshot_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
