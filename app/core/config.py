from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Banking Management System"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "mysql+pymysql://root:password@localhost:3306/enterprise_bank"

    jwt_secret_key: str = "change-this-secret-before-running"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    otp_expire_minutes: int = 10
    max_login_attempts: int = 5
    account_lock_minutes: int = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return init_settings, dotenv_settings, env_settings, file_secret_settings


@lru_cache
def get_settings() -> Settings:
    return Settings()
