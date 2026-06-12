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
CONF_ALL_VINS = "all_vins"  # all VINs discovered at setup, used by options flow

# BMW quota: 50 API calls/day per container. Each poll uses 1 call per VIN.
# Intervals chosen to stay safely under 50 calls/day including housekeeping.
SCAN_INTERVAL_BY_VIN_COUNT = {
    1: 35,   # ~41 polls/day
    2: 65,   # ~22 polls/day
    3: 100,  # ~14 polls/day
}
SCAN_INTERVAL_DEFAULT = 120  # 4+ VINs: ~12 polls/day

TYRE_DIAGNOSIS_REFRESH_HOURS = 23
TOKEN_REFRESH_BUFFER_SECONDS = 300

# Known-valid descriptors for container creation.
# Increment CONTAINER_NAME when this list changes to force container recreation.
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
    "vehicle.cabin.door.row1.driver.isOpen",
    "vehicle.cabin.door.row1.passenger.isOpen",
    "vehicle.cabin.door.row2.driver.isOpen",
    "vehicle.cabin.door.row2.passenger.isOpen",
    # Windows
    "vehicle.cabin.window.row1.driver.status",
    "vehicle.cabin.window.row1.passenger.status",
    "vehicle.cabin.window.row2.driver.status",
    "vehicle.cabin.window.row2.passenger.status",
    # Bonnet & boot
    "vehicle.body.hood.isOpen",
    "vehicle.body.trunk.isOpen",
    # Service
    "vehicle.status.serviceDistance.next",
    "vehicle.status.serviceTime.yellow",
    "vehicle.status.conditionBasedServices",
    "vehicle.status.checkControlMessages",
    # 12V battery
    "vehicle.electricalSystem.battery.voltage",
    "vehicle.electricalSystem.battery.stateOfCharge",
    "vehicle.electricalSystem.battery.serviceDemand.replace",
    "vehicle.electricalSystem.battery.serviceDemand.recharge",
    # Tyres
    "vehicle.chassis.axle.row1.wheel.left.tire.pressure",
    "vehicle.chassis.axle.row1.wheel.right.tire.pressure",
    "vehicle.chassis.axle.row2.wheel.left.tire.pressure",
    "vehicle.chassis.axle.row2.wheel.right.tire.pressure",
    # Engine & ignition
    "vehicle.drivetrain.engine.isActive",
    "vehicle.drivetrain.engine.isIgnitionOn",
    # Motion & lights
    "vehicle.isMoving",
    "vehicle.body.lights.isRunningOn",
    # Alarm
    "vehicle.vehicle.antiTheftAlarmSystem.alarm.isOn",
    "vehicle.vehicle.antiTheftAlarmSystem.alarm.armStatus",
    # Deep sleep
    "vehicle.vehicle.deepSleepModeActive",
]

CONTAINER_NAME = "home_assistant_ice_v3"
CONTAINER_PURPOSE = "Home Assistant BMW CarData integration"
