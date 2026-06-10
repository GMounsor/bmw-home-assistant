"""Sensor platform for BMW CarData."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VINS, DOMAIN
from .coordinator import BMWCoordinator

KM_TO_MILES = 0.621371


def _km_to_miles(v):
    if v is None:
        return None
    try:
        return round(float(v) * KM_TO_MILES, 1)
    except (ValueError, TypeError):
        return None


def _kmh_to_mph(v):
    if v is None:
        return None
    try:
        return round(float(v) * KM_TO_MILES, 1)
    except (ValueError, TypeError):
        return None


def _kpa_to_bar(v):
    if v is None:
        return None
    try:
        return round(float(v) / 100, 2)
    except (ValueError, TypeError):
        return None


def _float_round(v):
    if v is None:
        return None
    try:
        return round(float(v), 1)
    except (ValueError, TypeError):
        return None


def _int_val(v):
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class BMWSensorEntityDescription(SensorEntityDescription):
    descriptor: str = ""
    source: str = "telemetry"
    value_fn: Any = None


SENSORS = (
    BMWSensorEntityDescription(
        key="mileage",
        descriptor="vehicle.vehicle.travelledDistance",
        name="Mileage",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="fuel_level",
        descriptor="vehicle.drivetrain.fuelSystem.level",
        name="Fuel Level",
        icon="mdi:gas-station",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_int_val,
    ),
    BMWSensorEntityDescription(
        key="remaining_fuel_litres",
        descriptor="vehicle.drivetrain.fuelSystem.remainingFuel",
        name="Remaining Fuel",
        icon="mdi:gas-station-outline",
        native_unit_of_measurement="L",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="lifetime_fuel_consumed",
        descriptor="vehicle.drivetrain.fuelSystem.consumptionOverLifeTime.overall.fuel",
        name="Lifetime Fuel Consumed",
        icon="mdi:fuel",
        native_unit_of_measurement="L",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="remaining_range",
        descriptor="vehicle.cabin.infotainment.navigation.remainingRange",
        name="Remaining Range",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="last_remaining_range",
        descriptor="vehicle.drivetrain.lastRemainingRange",
        name="Last Reported Range",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="coolant_temp",
        descriptor="vehicle.drivetrain.internalCombustionEngine.engine.ect",
        name="Engine Coolant Temperature",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="battery_voltage",
        descriptor="vehicle.electricalSystem.battery.voltage",
        name="12V Battery Voltage",
        icon="mdi:car-battery",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="battery_soc",
        descriptor="vehicle.electricalSystem.battery.stateOfCharge",
        name="12V Battery Charge",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_int_val,
    ),
    BMWSensorEntityDescription(
        key="battery_health",
        descriptor="vehicle.electricalSystem.battery.serviceDemand.replace",
        name="12V Battery Health",
        icon="mdi:battery-heart",
    ),
    BMWSensorEntityDescription(
        key="tyre_fl_pressure",
        descriptor="vehicle.chassis.axle.row1.wheel.left.tire.pressure",
        name="Tyre Pressure Front Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_fr_pressure",
        descriptor="vehicle.chassis.axle.row1.wheel.right.tire.pressure",
        name="Tyre Pressure Front Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_rl_pressure",
        descriptor="vehicle.chassis.axle.row2.wheel.left.tire.pressure",
        name="Tyre Pressure Rear Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_rr_pressure",
        descriptor="vehicle.chassis.axle.row2.wheel.right.tire.pressure",
        name="Tyre Pressure Rear Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_fl_pressure_target",
        descriptor="vehicle.chassis.axle.row1.wheel.left.tire.pressureTarget",
        name="Tyre Target Pressure Front Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_fr_pressure_target",
        descriptor="vehicle.chassis.axle.row1.wheel.right.tire.pressureTarget",
        name="Tyre Target Pressure Front Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_rl_pressure_target",
        descriptor="vehicle.chassis.axle.row2.wheel.left.tire.pressureTarget",
        name="Tyre Target Pressure Rear Left",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_rr_pressure_target",
        descriptor="vehicle.chassis.axle.row2.wheel.right.tire.pressureTarget",
        name="Tyre Target Pressure Rear Right",
        icon="mdi:tire",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=_kpa_to_bar,
    ),
    BMWSensorEntityDescription(
        key="tyre_fl_temp",
        descriptor="vehicle.chassis.axle.row1.wheel.left.tire.temperature",
        name="Tyre Temperature Front Left",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="tyre_fr_temp",
        descriptor="vehicle.chassis.axle.row1.wheel.right.tire.temperature",
        name="Tyre Temperature Front Right",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="tyre_rl_temp",
        descriptor="vehicle.chassis.axle.row2.wheel.left.tire.temperature",
        name="Tyre Temperature Rear Left",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="tyre_rr_temp",
        descriptor="vehicle.chassis.axle.row2.wheel.right.tire.temperature",
        name="Tyre Temperature Rear Right",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="service_distance",
        descriptor="vehicle.status.serviceDistance.next",
        name="Next Service Distance",
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="service_due_date",
        descriptor="vehicle.status.serviceTime.yellow",
        name="Service Due Date",
        icon="mdi:calendar-wrench",
    ),
    BMWSensorEntityDescription(
        key="condition_based_services",
        descriptor="vehicle.status.conditionBasedServices",
        name="Condition Based Services",
        icon="mdi:clipboard-check",
    ),
    BMWSensorEntityDescription(
        key="check_control",
        descriptor="vehicle.status.checkControlMessages",
        name="Check Control Messages",
        icon="mdi:alert-circle",
    ),
    BMWSensorEntityDescription(
        key="alarm_arm_status",
        descriptor="vehicle.vehicle.antiTheftAlarmSystem.alarm.armStatus",
        name="Alarm Status",
        icon="mdi:shield-car",
    ),
    BMWSensorEntityDescription(
        key="door_lock_status",
        descriptor="vehicle.cabin.door.lock.status",
        name="Door Lock Status",
        icon="mdi:car-door-lock",
    ),
    BMWSensorEntityDescription(
        key="door_status",
        descriptor="vehicle.cabin.door.status",
        name="Door Status",
        icon="mdi:car-door",
    ),
    BMWSensorEntityDescription(
        key="avg_speed",
        descriptor="vehicle.vehicle.avgSpeed",
        name="Average Speed",
        icon="mdi:speedometer",
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_kmh_to_mph,
    ),
    BMWSensorEntityDescription(
        key="last_trip_distance",
        descriptor="vehicle.trip.segment.end.traveledDistance",
        name="Last Trip Distance",
        icon="mdi:map-marker-path",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="last_trip_time",
        descriptor="vehicle.trip.segment.end.time",
        name="Last Trip Time",
        icon="mdi:clock-end",
    ),
    BMWSensorEntityDescription(
        key="driving_score_acceleration",
        descriptor="vehicle.trip.segment.accumulated.acceleration.starsAverage",
        name="Driving Score Acceleration",
        icon="mdi:star",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="driving_score_braking",
        descriptor="vehicle.trip.segment.accumulated.chassis.brake.starsAverage",
        name="Driving Score Braking",
        icon="mdi:star",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_float_round,
    ),
    BMWSensorEntityDescription(
        key="weekly_distance_short",
        descriptor="vehicle.vehicle.averageWeeklyDistanceShortTerm",
        name="Weekly Distance Short Term",
        icon="mdi:road",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="weekly_distance_long",
        descriptor="vehicle.vehicle.averageWeeklyDistanceLongTerm",
        name="Weekly Distance Long Term",
        icon="mdi:road",
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_km_to_miles,
    ),
    BMWSensorEntityDescription(
        key="dtc",
        descriptor="vehicle.electronicControlUnit.diagnosticTroubleCodes.raw",
        name="Fault Codes DTC",
        icon="mdi:wrench-check",
    ),
    BMWSensorEntityDescription(
        key="sim_status",
        descriptor="vehicle.sim.status",
        name="SIM Status",
        icon="mdi:sim",
    ),
    BMWSensorEntityDescription(
        key="tyre_diagnosis",
        descriptor="",
        source="tyre_diagnosis",
        name="Tyre Diagnosis",
        icon="mdi:tire",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    vins = entry.data[CONF_VINS]
    entities = [
        BMWSensorEntity(coordinator, vin, description)
        for vin in vins
        for description in SENSORS
    ]
    async_add_entities(entities)


class BMWSensorEntity(CoordinatorEntity, SensorEntity):
    """A single BMW telemetry sensor."""

    def __init__(self, coordinator, vin, description):
        super().__init__(coordinator)
        self._vin = vin
        self.entity_description = description
        self._attr_unique_id = f"{vin}_{description.key}"
        self._attr_name = f"BMW {vin[-4:]} {description.name}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": f"BMW ({vin})",
            "manufacturer": "BMW",
        }

    def _vin_data(self):
        return (self.coordinator.data or {}).get(self._vin, {})

    @property
    def native_value(self):
        desc = self.entity_description
        if desc.source == "tyre_diagnosis":
            td = self._vin_data().get("tyre_diagnosis", {})
            return td.get("overallStatus") or ("OK" if td else None)
        telemetry = self._vin_data().get("telemetry", {})
        entry = telemetry.get(desc.descriptor)
        if entry is None:
            return None
        raw = entry.get("value")
        if raw is None:
            return None
        try:
            return desc.value_fn(raw) if desc.value_fn else raw
        except (ValueError, TypeError):
            return raw

    @property
    def extra_state_attributes(self):
        desc = self.entity_description
        if desc.source == "tyre_diagnosis":
            td = self._vin_data().get("tyre_diagnosis", {})
            return {k: v for k, v in td.items() if k != "overallStatus"} if td else {}
        telemetry = self._vin_data().get("telemetry", {})
        entry = telemetry.get(desc.descriptor, {})
        return {k: v for k, v in entry.items() if k != "value" and v is not None}
