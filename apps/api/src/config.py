from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://credit:credit@localhost:5432/credit_spread"

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    moomoo_host: str = "127.0.0.1"
    moomoo_port: int = 11111
    moomoo_trade_pwd: str = ""
    moomoo_security_firm: str = "FUTUSG"
    moomoo_trd_market: str = "US"

    snapshot_cron: str = "*/5 9-16 * * mon-fri"
    snapshot_tz: str = "America/New_York"


@lru_cache
def get_settings() -> Settings:
    return Settings()
