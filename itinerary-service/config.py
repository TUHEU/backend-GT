"""Configuration - itinerary-service (Phase 2)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = os.getenv("SECRET_KEY", "yaounde-ensemble-phase2-secret-change-me")
ALGORITHM = "HS256"

ITINERARIES_FILE = DATA_DIR / "itineraries.json"

PORT = int(os.getenv("PORT", 5012))

RECOMMENDATION_SERVICE_URL = os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:5013")
