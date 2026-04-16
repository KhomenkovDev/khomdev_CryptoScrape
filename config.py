from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    APP_NAME: str = "BrandMonitor"
    GEMINI_API_KEY: Optional[str] = None
    LOG_LEVEL: str = "INFO"

    # Scraper settings
    SCRAPE_TIMEOUT: int = 30000  # ms
    HEADLESS: bool = True

    # Demo Mode
    # If True, the app will return mock data if Gemini API fails or is missing
    DEMO_MODE: bool = False

    # Social Media credentials (stored only in local .env — never shared)
    X_USERNAME: Optional[str] = None
    X_PASSWORD: Optional[str] = None
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Post-init check to auto-enable demo mode if key is missing
if not settings.GEMINI_API_KEY:
    settings.DEMO_MODE = True
