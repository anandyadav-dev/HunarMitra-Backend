from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hunar Mitra App Backend"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:password@localhost:3306/hunarmitra",
        description="Database connection URL."
    )
    
    JWT_SECRET_KEY: str = Field(
        default="hunarmitra-secret-key-321-prod-grade-app",
        description="Secret key to sign JWT tokens"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    
    OTP_EXPIRE_MINUTES: int = 5
    DEBUG_OTP: bool = True
    
    PAYMENT_GATEWAY_KEY: str = Field(
        default="rzp_test_hunarmitra_mock",
        description="Payment gateway client Key ID"
    )
    PAYMENT_WEBHOOK_SECRET: str = Field(
        default="hunarmitra_webhook_secret_key_123",
        description="Secret key to verify payment gateway webhook signatures"
    )
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
