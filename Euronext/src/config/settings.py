# src/config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration API
class APIConfig:
    BASE_URL = os.getenv("API_BASE_URL", "https://api.example.com")
    API_KEY = os.getenv("API_KEY", "")
    TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    
    # Rate limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS", "30"))
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 heure
    
    # Retry strategy
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "1.0"))

# Configuration application
class AppConfig:
    APP_NAME = "Analyse Financière MC.PA"
    APP_ICON = "📊"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"

# Symboles par défaut
DEFAULT_SYMBOLS = ["MC.PA", "RMS.PA", "KER.PA"]