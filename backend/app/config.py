from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Configuration settings for the application."""
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "test_key")
    shopify_api_secret: str = os.getenv("SHOPIFY_API_SECRET", "test_secret")
    shopify_redirect_uri: str = os.getenv(
        "SHOPIFY_REDIRECT_URI", "http://localhost:8000/auth/shopify/callback"
    )
    
    # VLM Extraction Settings
    extraction_backend: str = os.getenv("EXTRACTION_BACKEND", "mock")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    fine_tuned_model_path: str = os.getenv("FINE_TUNED_MODEL_PATH", "")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
