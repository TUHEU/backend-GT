"""Configuration - recommendation-service (Phase 2)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

SECRET_KEY = os.getenv("SECRET_KEY", "yaounde-ensemble-phase2-secret-change-me")
ALGORITHM = "HS256"

DESTINATIONS_FILE = DATA_DIR / "destinations.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"

PORT = int(os.getenv("PORT", 5013))

# Other services this one calls over the network (service discovery is
# hardcoded via Docker Compose service names for this phase - a real
# service registry like Consul/Eureka comes later).
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5011")
ITINERARY_SERVICE_URL = os.getenv("ITINERARY_SERVICE_URL", "http://itinerary-service:5012")
