import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "National Land Acquisition & Management System"
    APP_SHORT_NAME: str = "LAMS"
    VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lams_user:lams_password@localhost:5432/lams_db"

    # Security & JWT
    JWT_SECRET_KEY: str = "lams_dev_secret_key_change_in_production_2026_super_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Seed Admin Credentials
    SEED_ADMIN_EMAIL: str = "admin.national@lams.gov.in"
    SEED_ADMIN_PASSWORD: str = "LamsAdmin@2026"

    # CORS Origins configuration - allow all origins for cloud deployments
    CORS_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
