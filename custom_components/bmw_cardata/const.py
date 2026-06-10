"""Constants for the BMW CarData integration."""

DOMAIN = "bmw_cardata"

# ── OAuth / Auth ──────────────────────────────────────────────────────────────
AUTH_BASE_URL = "https://customer.bmwgroup.com"
DEVICE_CODE_URL = f"{AUTH_BASE_URL}/gcdm/oauth/device/code"
TOKEN_URL = f"{AUTH_BASE_URL}/gcdm/oauth/token"
OAUTH_SCOPE = "authenticate_user openid cardata:api:read"
GRANT_TYPE_DEVICE = "urn:ietf:params:oauth:grant-type:device_code"

# ── REST API ──────────────────────────────────────────────────────────────────
API_BASE_URL = "https://api-cardata.bmwgroup.com"
API_VERSION_HEADER = {"x-version": "v1"}

# ── Config entry keys ─────────────────────────────────────────────────────────
CONF_CLIENT_ID = "client_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_EXPIRES_AT = "token_expires_at"
CONF_CONTAINER_ID = "container_id"
CONF_VINS = "vins"

# ── Timing ────────────────────────────────────────────────────────────────────
# BMW allows 50 API calls/day.  30-minute polling = 48 calls/day max.
SCAN_INTERVAL_MINUTES = 30
# Refresh the access token when it has less than this many seconds left.
TOKEN_REFRESH_BUFFER_SECONDS = 300

# ── Telemetry descriptors to subscribe to ────────────────────────────────────
# These are the BMW descriptor IDs that will be included in our data container.
# Focused on ICE (petrol/diesel) vehicles – EV/charging fields are excluded.
DESCRIPTORS = [
    # Odometer
    "vehicle.vehicle.travelledDistance",
    # Fuel
    "vehicle.drivetrain.fuelSystem.level",
    "vehicle.drivetrain.fuelSystem.remainingFuel",
    # Range
    "vehicle.cabin.infotainment.navigation.remainingRange",
    # GPS
    "vehicle.cabin.infotainment.navigation.currentLocation.latitude",
    "vehicle.cabin.infotainment.navigation.currentLocation.longitude",
    "vehicle.cabin.infotainment.navigation.currentLocation.heading",
    # Doors
    "vehicle.cabin.door.row1.driver.isOpen",
    "vehicle.cabin.door.row1.passenger.isOpen",
    "vehicle.cabin.door.row2.driver.isOpen",
    "vehicle.cabin.door.row2.passenger.isOpen",
    "vehicle.cabin.door.status",
    # Locks
    "vehicle.cabin.door.lock.status",
    # Boot & bonnet
    "vehicle.body.hood.isOpen",
    "vehicle.body.trunk.isOpen",
    # Windows
    "vehicle.cabin.window.row1.driver.status",
    "vehicle.cabin.window.row1.passenger.status",
    "vehicle.cabin.window.row2.driver.status",
    "vehicle.cabin.window.row2.passenger.status",
    # Service
    "vehicle.status.serviceDistance.next",
    "vehicle.status.serviceTime.yellow",
    # Alarm
    "vehicle.vehicle.antiTheftAlarmSystem.alarm.isOn",
    "vehicle.vehicle.antiTheftAlarmSystem.alarm.armStatus",
]

CONTAINER_NAME = "home_assistant_ice"
CONTAINER_PURPOSE = "Home Assistant BMW CarData integration – ICE vehicle telemetry"
