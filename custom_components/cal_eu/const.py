"""Constants for the Cal.eu integration."""

DOMAIN = "cal_eu"

CONF_API_KEY = "api_key"

API_BASE_URL = "https://api.cal.eu/v2"
API_BOOKINGS_ENDPOINT = "/bookings"

DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

EVENT_NEW_BOOKING = "cal_eu_new_booking"

# HTTP Status Codes
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401

# Booking Status (API returns uppercase)
BOOKING_STATUS_ACCEPTED = "ACCEPTED"
BOOKING_STATUS_PENDING = "PENDING"
