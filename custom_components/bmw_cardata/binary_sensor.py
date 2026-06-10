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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VINS, DOMAIN
from .coordinator import BMWCoordinator

# BMW uses various truthy string values
_TRUE_VALUES = {"true", "1", "yes", "open", "OPEN"}
_FALSE_VALUES = {"false", "0", "no", "closed", "CLOSED"}


def _parse_bool(value: str | None) -> bool | None:
    """Parse a BMW string boolean/state into a Python bool."""
    if value is None:
        return None
    lower = value.lower()
    if lower in _TRUE_VALUES:
        return True
    if lower in _FALSE_VALUES:
        return False
    return None


@dataclass(frozen=True, kw_only=True)
class BMWBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Extends BinarySensorEntityDescription with a BMW descriptor key."""
    descriptor: str
    # Optional: if the "true" state means something specific
    true_value: str | None = None


BINARY_SENSORS: tuple[BMWBinarySensorEntityDescription, ...] = (
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMW CarData binary sensor entities."""
    coordinator: BMWCoordinator = hass.data[DOMAIN][entry.entry_id]
    vins: list[str] = entry.data[CONF_VINS]

    entities = [
        BMWBinarySensorEntity(coordinator, vin, description)
        for vin in vins
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)


class BMWBinarySensorEntity(CoordinatorEntity[BMWCoordinator], BinarySensorEntity):
    """A single BMW binary telemetry sensor."""

    entity_description: BMWBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: BMWCoordinator,
        vin: str,
        description: BMWBinarySensorEntityDescription,
    ) -> None:
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
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is active/open."""
        vin_data: dict[str, Any] = (self.coordinator.data or {}).get(self._vin, {})
        entry = vin_data.get(self.entity_description.descriptor)
        if entry is None:
            return None
        raw = entry.get("value")
        return _parse_bool(raw)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        vin_data: dict[str, Any] = (self.coordinator.data or {}).get(self._vin, {})
        entry = vin_data.get(self.entity_description.descriptor, {})
        return {k: v for k, v in entry.items() if k != "value" and v is not None}
