from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Configuration settings for the application."""
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "")
    shopify_api_secret: str = os.getenv("SHOPIFY_API_SECRET", "")
    shopify_redirect_uri: str = os.getenv(
        "SHOPIFY_REDIRECT_URI", "http://localhost:3000/auth/callback"
    )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
