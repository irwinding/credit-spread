from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import legs as legs_router
from .api import snapshot as snapshot_router
from .api import spreads as spreads_router
from .config import Settings, get_settings
from .moomoo_client import MoomooClient
from .scheduler import build_snapshot_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

CORS_ORIGINS = ["http://localhost:5174", "http://127.0.0.1:5174"]


def build_moomoo_client(settings: Settings) -> MoomooClient:
    return MoomooClient(
        host=settings.moomoo_host,
        port=settings.moomoo_port,
        trade_pwd=settings.moomoo_trade_pwd,
        security_firm=settings.moomoo_security_firm,
        trd_market=settings.moomoo_trd_market,
    )


def configure_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_routes(app: FastAPI) -> None:
    app.include_router(spreads_router.router)
    app.include_router(legs_router.router)
    app.include_router(snapshot_router.router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.moomoo_client = build_moomoo_client(settings)
    scheduler = build_snapshot_scheduler(settings, app.state.moomoo_client)
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("scheduler started: cron=%r tz=%s", settings.snapshot_cron, settings.snapshot_tz)
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="credit-spread API", version="0.1.0", lifespan=lifespan)
configure_cors(app)
register_routes(app)


@app.get("/health")
def health():
    return {"status": "ok"}
