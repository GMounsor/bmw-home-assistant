"""Constants for the BMW CarData integration."""

DOMAIN = "bmw_cardata"

AUTH_BASE_URL = "https://customer.bmwgroup.com"
DEVICE_CODE_URL = f"{AUTH_BASE_URL}/gcdm/oauth/device/code"
TOKEN_URL = f"{AUTH_BASE_URL}/gcdm/oauth/token"
OAUTH_SCOPE = "authenticate_user openid cardata:api:read"
GRANT_TYPE_DEVICE = "urn:ietf:params:oauth:grant-type:device_code"

API_BASE_URL = "https://api-cardata.bmwgroup.com"
API_VERSION_HEADER = {"x-version": "v1"}

CONF_CLIENT_ID = "client_id"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_EXPIRES_AT = "token_expires_at"
CONF_CONTAINER_ID = "container_id"
CONF_VINS = "vins"

SCAN_INTERVAL_MINUTES = 30
TYRE_DIAGNOSIS_REFRESH_HOURS = 23
TOKEN_REFRESH_BUFFER_SECONDS = 300

# Core descriptors known to be supported by the BMW CarData API.
# These are used as a hint when creating the telemetry container.
# If BMW rejects them (CU-402), the container is created without specifying
# descriptors and BMW uses whatever the user configured in the portal.
DESCRIPTORS = [
    # Odometer & range
    "vehicle.vehicle.travelledDistance",
    "vehicle.cabin.infotainment.navigation.remainingRange",
    # Fuel
    "vehicle.drivetrain.fuelSystem.level",
    "vehicle.drivetrain.fuelSystem.remainingFuel",
    # Location
    "vehicle.cabin.infotainment.navigation.currentLocation.latitude",
    "vehicle.cabin.infotainment.navigation.currentLocation.longitude",
    "vehicle.cabin.infotainment.navigation.currentLocation.heading",
    # Doors & locks
    "vehicle.cabin.door.status",
    "vehicle.cabin.door.lock.status",
    # Service
    "vehicle.status.serviceDistance.next",
    "vehicle.status.serviceTime.yellow",
    "vehicle.status.conditionBasedServices",
    "vehicle.status.checkControlMessages",
    # 12V battery
    "vehicle.electricalSystem.battery.voltage",
    "vehicle.electricalSystem.battery.stateOfCharge",
    # Tyres
    "vehicle.chassis.axle.row1.wheel.left.tire.pressure",
    "vehicle.chassis.axle.row1.wheel.right.tire.pressure",
    "vehicle.chassis.axle.row2.wheel.left.tire.pressure",
    "vehicle.chassis.axle.row2.wheel.right.tire.pressure",
]

CONTAINER_NAME = "home_assistant_ice"
CONTAINER_PURPOSE = "Home Assistant BMW CarData integration"
