# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class APIConfig:
    BASE_URL = os.getenv("API_BASE_URL", "https://api.example.com")
    API_KEY = os.getenv("API_KEY", "")
    TIMEOUT = 30
    MAX_REQUESTS_PER_MINUTE = 30
    CACHE_TTL = 3600
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 1.0

class AppConfig:
    APP_NAME = "Analyse Financière MC.PA"
    APP_ICON = "📊"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"

DEFAULT_SYMBOLS = ["MC.PA", "RMS.PA", "KER.PA"]
