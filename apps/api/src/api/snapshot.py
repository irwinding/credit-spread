from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import SpreadSnapshot
from ..schemas import SnapshotResult, SnapshotStatus
from ..snapshotter import run_snapshot

router = APIRouter(prefix="/snapshot", tags=["snapshot"])


@router.post("/run", response_model=SnapshotResult)
def trigger_snapshot(request: Request, db: Session = Depends(get_db)):
    client = getattr(request.app.state, "moomoo_client", None)
    if client is None:
        raise HTTPException(503, "moomoo client not configured")
    rows = run_snapshot(db, client)
    return SnapshotResult(rows_written=rows, ts=datetime.now(timezone.utc))


@router.get("/status", response_model=SnapshotStatus)
def snapshot_status(request: Request, db: Session = Depends(get_db)):
    scheduler = getattr(request.app.state, "scheduler", None)
    next_run_at: datetime | None = None
    if scheduler is not None:
        job = scheduler.get_job("snapshot")
        if job is not None and job.next_run_time is not None:
            next_run_at = job.next_run_time.astimezone(timezone.utc)

    last_ts = db.scalar(select(SpreadSnapshot.ts).order_by(SpreadSnapshot.ts.desc()).limit(1))
    return SnapshotStatus(
        next_run_at=next_run_at,
        last_snapshot_at=last_ts,
        server_time=datetime.now(timezone.utc),
    )
