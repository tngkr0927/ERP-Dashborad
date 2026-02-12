from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+asyncpg://erp_user:erp_pass@db:5432/erp_dashboard"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://erp_user:erp_pass@db:5432/erp_dashboard"
    )

    class Config:
        env_file = ".env"


settings = Settings()
