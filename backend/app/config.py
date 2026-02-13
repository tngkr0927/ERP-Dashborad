from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = (
        "postgresql+asyncpg://erp_user:erp_pass@db:5432/erp_dashboard"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://erp_user:erp_pass@db:5432/erp_dashboard"
    )

    # Gemini API 키 — .env 파일에 GEMINI_API_KEY=your_key_here 를 설정하세요.
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
