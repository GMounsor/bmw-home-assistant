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

DESCRIPTORS = [
    "vehicle.vehicle.travelledDistance",
    "vehicle.drivetrain.fuelSystem.level",
    "vehicle.drivetrain.fuelSystem.remainingFuel",
    "vehicle.drivetrain.fuelSystem.consumptionOverLifeTime.overall.fuel",
    "vehicle.drivetrain.fuelSystem.consumptionOverLifeTime.overall.referenceDistance",
    "vehicle.cabin.infotainment.navigation.remainingRange",
    "vehicle.drivetrain.lastRemainingRange",
    "vehicle.drivetrain.engine.isActive",
    "vehicle.drivetrain.engine.isIgnitionOn",
    "vehicle.drivetrain.internalCombustionEngine.engine.ect",
    "vehicle.isMoving",
    "vehicle.cabin.infotainment.navigation.currentLocation.latitude",
    "vehicle.cabin.infotainment.navigation.currentLocation.longitude",
    "vehicle.cabin.infotainment.navigation.currentLocation.heading",
    "vehicle.cabin.door.row1.driver.isOpen",
    "vehicle.cabin.door.row1.passenger.isOpen",
    "vehicle.cabin.door.row2.driver.isOpen",
    "vehicle.cabin.door.row2.passenger.isOpen",
    "vehicle.cabin.door.status",
    "vehicle.cabin.door.lock.status",
    "vehicle.body.hood.isOpen",
    "vehicle.body.trunk.isOpen",
    "vehicle.cabin.window.row1.driver.status",
    "vehicle.cabin.window.row1.passenger.status",
    "vehicle.cabin.window.row2.driver.status",
    "vehicle.cabin.window.row2.passenger.status",
    "vehicle.body.lights.isRunningOn",
    "vehicle.electricalSystem.battery.voltage",
    "vehicle.electricalSystem.battery.stateOfCharge",
    "vehicle.electricalSystem.battery.serviceDemand.replace",
    "vehicle.electricalSystem.battery.serviceDemand.recharge",
    "vehicle.chassis.axle.row1.wheel.left.tire.pressure",
    "vehicle.chassis.axle.row1.wheel.right.tire.pressure",
    "vehicle.chassis.axle.row2.wheel.left.tire.pressure",
    "vehicle.chassis.axle.row2.wheel.right.tire.pressure",
    "vehicle.chassis.axle.row1.wheel.left.tire.pressureTarget",
    "vehicle.chassis.axle.row1.wheel.right.tire.pressureTarget",
    "vehicle.chassis.axle.row2.wheel.left.tire.pressureTarget",
    "vehicle.chassis.axle.row2.wheel.right.tire.pressureTarget",
    "vehicle.chassis.axle.row1.wheel.left.tire.temperature",
    "vehicle.chassis.axle.row1.wheel.right.tire.temperature",
    "vehicle.chassis.axle.row2.wheel.left.tire.temperature",
    "vehicle.chassis.axle.row2.wheel.right.tire.temperature",
    "vehicle.status.serviceDistance.next",
    "vehicle.status.serviceTime.yellow",
    "vehicle.status.conditionBasedServices",
    "vehicle.status.checkControlMessages",
    "vehicle.vehicle.antiTheftAlarmSystem.alarm.isOn",
    "vehicle.vehicle.antiTheftAlarmSystem.alarm.armStatus",
    "vehicle.vehicle.avgSpeed",
    "vehicle.trip.segment.end.traveledDistance",
    "vehicle.trip.segment.end.time",
    "vehicle.trip.segment.accumulated.acceleration.starsAverage",
    "vehicle.trip.segment.accumulated.chassis.brake.starsAverage",
    "vehicle.vehicle.averageWeeklyDistanceShortTerm",
    "vehicle.vehicle.averageWeeklyDistanceLongTerm",
    "vehicle.electronicControlUnit.diagnosticTroubleCodes.raw",
    "vehicle.vehicle.deepSleepModeActive",
    "vehicle.sim.status",
]

CONTAINER_NAME = "home_assistant_ice"
CONTAINER_PURPOSE = "Home Assistant BMW CarData integration - ICE vehicle telemetry"
