from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Arontier Groupware"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SECRET_KEY: str = "arontier-groupware-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./groupware.db"

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_prefix": "", "case_sensitive": True}


settings = Settings()
