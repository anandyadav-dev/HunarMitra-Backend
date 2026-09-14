from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hunar Mitra App Backend"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = Field(
        default="sqlite:///./hunarmitra.db",
        description="Database connection URL. Defaults to a local SQLite file for development when MySQL is unavailable."
    )
    
    JWT_SECRET_KEY: str = Field(
        default="hunarmitra-secret-key-321-prod-grade-app",
        description="Secret key to sign JWT tokens"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    
    OTP_EXPIRE_MINUTES: int = 5
    DEBUG_OTP: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
