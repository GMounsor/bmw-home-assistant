"""Binary sensor platform for BMW CarData."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VINS, DOMAIN
from .coordinator import BMWCoordinator

_TRUE_VALUES = {"true", "1", "yes", "open", "on", "active"}
_FALSE_VALUES = {"false", "0", "no", "closed", "off"}


def _parse_bool(value):
    if value is None:
        return None
    if value.lower() in _TRUE_VALUES:
        return True
    if value.lower() in _FALSE_VALUES:
        return False
    return None


@dataclass(frozen=True, kw_only=True)
class BMWBinarySensorEntityDescription(BinarySensorEntityDescription):
    descriptor: str = ""


BINARY_SENSORS = (
    BMWBinarySensorEntityDescription(
        key="engine_active",
        descriptor="vehicle.drivetrain.engine.isActive",
        name="Engine Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine",
    ),
    BMWBinarySensorEntityDescription(
        key="ignition_on",
        descriptor="vehicle.drivetrain.engine.isIgnitionOn",
        name="Ignition",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:key",
    ),
    BMWBinarySensorEntityDescription(
        key="is_moving",
        descriptor="vehicle.isMoving",
        name="Moving",
        device_class=BinarySensorDeviceClass.MOTION,
        icon="mdi:car-arrow-right",
    ),
    BMWBinarySensorEntityDescription(
        key="lights_on",
        descriptor="vehicle.body.lights.isRunningOn",
        name="Lights",
        device_class=BinarySensorDeviceClass.LIGHT,
        icon="mdi:car-light-high",
    ),
    BMWBinarySensorEntityDescription(
        key="door_row1_driver",
        descriptor="vehicle.cabin.door.row1.driver.isOpen",
        name="Door Front Driver",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    BMWBinarySensorEntityDescription(
        key="door_row1_passenger",
        descriptor="vehicle.cabin.door.row1.passenger.isOpen",
        name="Door Front Passenger",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    BMWBinarySensorEntityDescription(
        key="door_row2_driver",
        descriptor="vehicle.cabin.door.row2.driver.isOpen",
        name="Door Rear Driver",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    BMWBinarySensorEntityDescription(
        key="door_row2_passenger",
        descriptor="vehicle.cabin.door.row2.passenger.isOpen",
        name="Door Rear Passenger",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    BMWBinarySensorEntityDescription(
        key="hood_open",
        descriptor="vehicle.body.hood.isOpen",
        name="Bonnet",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:car-raised-hood",
    ),
    BMWBinarySensorEntityDescription(
        key="trunk_open",
        descriptor="vehicle.body.trunk.isOpen",
        name="Boot",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:car-back",
    ),
    BMWBinarySensorEntityDescription(
        key="window_row1_driver",
        descriptor="vehicle.cabin.window.row1.driver.status",
        name="Window Front Driver",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-side",
    ),
    BMWBinarySensorEntityDescription(
        key="window_row1_passenger",
        descriptor="vehicle.cabin.window.row1.passenger.status",
        name="Window Front Passenger",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-side",
    ),
    BMWBinarySensorEntityDescription(
        key="window_row2_driver",
        descriptor="vehicle.cabin.window.row2.driver.status",
        name="Window Rear Driver",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-side",
    ),
    BMWBinarySensorEntityDescription(
        key="window_row2_passenger",
        descriptor="vehicle.cabin.window.row2.passenger.status",
        name="Window Rear Passenger",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-side",
    ),
    BMWBinarySensorEntityDescription(
        key="alarm_active",
        descriptor="vehicle.vehicle.antiTheftAlarmSystem.alarm.isOn",
        name="Alarm Active",
        device_class=BinarySensorDeviceClass.TAMPER,
        icon="mdi:alarm-light",
    ),
    BMWBinarySensorEntityDescription(
        key="battery_recharge_needed",
        descriptor="vehicle.electricalSystem.battery.serviceDemand.recharge",
        name="12V Battery Recharge Needed",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-low",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BMWBinarySensorEntityDescription(
        key="deep_sleep",
        descriptor="vehicle.vehicle.deepSleepModeActive",
        name="Deep Sleep Mode",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:sleep",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # EV / PHEV
    BMWBinarySensorEntityDescription(
        key="charging_active",
        descriptor="vehicle.drivetrain.chargingSystem.isActive",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
    ),
    BMWBinarySensorEntityDescription(
        key="plug_connected",
        descriptor="vehicle.drivetrain.chargingSystem.isConnected",
        name="Plug Connected",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:ev-plug-type2",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    vins = entry.data[CONF_VINS]
    entities = [
        BMWBinarySensorEntity(coordinator, vin, description)
        for vin in vins
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)


class BMWBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """A single BMW binary sensor."""

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

    @property
    def is_on(self):
        telemetry = (self.coordinator.data or {}).get(self._vin, {}).get("telemetry", {})
        entry = telemetry.get(self.entity_description.descriptor)
        if entry is None:
            return None
        return _parse_bool(entry.get("value"))

    @property
    def extra_state_attributes(self):
        telemetry = (self.coordinator.data or {}).get(self._vin, {}).get("telemetry", {})
        entry = telemetry.get(self.entity_description.descriptor, {})
        return {k: v for k, v in entry.items() if k != "value" and v is not None}
