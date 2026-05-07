from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .db import SessionLocal
from .moomoo_client import MoomooClient
from .snapshotter import run_snapshot

logger = logging.getLogger(__name__)

CRON_FIELDS = ("minute", "hour", "day", "month", "day_of_week")


def parse_cron(expr: str) -> dict[str, str]:
    parts = expr.split()
    if len(parts) != len(CRON_FIELDS):
        raise ValueError(f"SNAPSHOT_CRON must be 5 fields, got: {expr!r}")
    return dict(zip(CRON_FIELDS, parts))


def _run_scheduled_snapshot(client: MoomooClient) -> None:
    db = SessionLocal()
    try:
        run_snapshot(db, client)
    except Exception:
        logger.exception("scheduled snapshot failed")
    finally:
        db.close()


def build_snapshot_scheduler(settings: Settings, client: MoomooClient) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.snapshot_tz)
    scheduler.add_job(
        _run_scheduled_snapshot,
        CronTrigger(**parse_cron(settings.snapshot_cron), timezone=settings.snapshot_tz),
        args=[client],
        id="snapshot",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
