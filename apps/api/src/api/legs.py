from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import LegSnapshot, OptionLeg
from ..schemas import LegHistory, LegOut, LegSnapshotPoint

router = APIRouter(prefix="/legs", tags=["legs"])


def _attach_latest_mark(db: Session, leg: OptionLeg) -> OptionLeg:
    latest = db.scalar(
        select(LegSnapshot)
        .where(LegSnapshot.leg_id == leg.id)
        .order_by(LegSnapshot.ts.desc())
        .limit(1)
    )
    if latest is not None:
        leg.last_mark = latest.mid  # type: ignore[attr-defined]
        leg.last_bid = latest.bid  # type: ignore[attr-defined]
        leg.last_ask = latest.ask  # type: ignore[attr-defined]
        leg.last_mark_ts = latest.ts  # type: ignore[attr-defined]
    return leg


@router.get("", response_model=list[LegOut])
def list_legs(
    ungrouped_only: bool = False,
    include_closed: bool = False,
    db: Session = Depends(get_db),
):
    stmt = select(OptionLeg).order_by(OptionLeg.expiry.asc(), OptionLeg.strike.asc())
    if not include_closed:
        stmt = stmt.where(OptionLeg.closed_at.is_(None))
    if ungrouped_only:
        stmt = stmt.where(OptionLeg.spread_id.is_(None))
    legs = db.scalars(stmt).all()
    for leg in legs:
        _attach_latest_mark(db, leg)
    return legs


@router.get("/{leg_id}/history", response_model=LegHistory)
def leg_history(leg_id: int, db: Session = Depends(get_db)):
    leg = db.get(OptionLeg, leg_id)
    if leg is None:
        raise HTTPException(404, "leg not found")
    rows = db.scalars(
        select(LegSnapshot)
        .where(LegSnapshot.leg_id == leg_id)
        .order_by(LegSnapshot.ts.asc())
    ).all()
    return LegHistory(
        leg_id=leg_id,
        points=[
            LegSnapshotPoint(ts=r.ts, bid=r.bid, ask=r.ask, mid=r.mid) for r in rows
        ],
    )
