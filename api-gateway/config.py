"""Configuration - api-gateway (Phase 2)."""
import os

PORT = int(os.getenv("PORT", 5003))

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5011")
ITINERARY_SERVICE_URL = os.getenv("ITINERARY_SERVICE_URL", "http://itinerary-service:5012")
RECOMMENDATION_SERVICE_URL = os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:5013")
CHAT_SERVICE_URL = os.getenv("CHAT_SERVICE_URL", "http://chat-service:5014")

REQUEST_TIMEOUT = 5
