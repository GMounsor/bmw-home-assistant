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
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VINS, DOMAIN
from .coordinator import BMWCoordinator


@dataclass(frozen=True, kw_only=True)
class BMWSensorEntityDescription(SensorEntityDescription):
    """Extends SensorEntityDescription with a BMW descriptor key."""
    descriptor: str
    value_fn: Any = None  # optional callable to transform raw string value


SENSORS: tuple[BMWSensorEntityDescription, ...] = (
    BMWSensorEntityDescription(
        key="mileage",
        descriptor="vehicle.vehicle.travelledDistance",
        name="Mileage",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda v: round(float(v)) if v else None,
    ),
    BMWSensorEntityDescription(
        key="fuel_level",
        descriptor="vehicle.drivetrain.fuelSystem.level",
        name="Fuel Level",
        icon="mdi:gas-station",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda v: round(float(v)) if v else None,
    ),
    BMWSensorEntityDescription(
        key="remaining_fuel",
        descriptor="vehicle.drivetrain.fuelSystem.remainingFuel",
        name="Remaining Fuel",
        icon="mdi:gas-station-outline",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,  # BMW reports km remaining
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda v: round(float(v)) if v else None,
    ),
    BMWSensorEntityDescription(
        key="remaining_range",
        descriptor="vehicle.cabin.infotainment.navigation.remainingRange",
        name="Remaining Range",
        icon="mdi:map-marker-distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda v: round(float(v)) if v else None,
    ),
    BMWSensorEntityDescription(
        key="service_distance",
        descriptor="vehicle.status.serviceDistance.next",
        name="Next Service Distance",
        icon="mdi:wrench-clock",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda v: int(v) if v else None,
    ),
    BMWSensorEntityDescription(
        key="service_due_date",
        descriptor="vehicle.status.serviceTime.yellow",
        name="Service Due Date",
        icon="mdi:calendar-wrench",
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
        key="alarm_arm_status",
        descriptor="vehicle.vehicle.antiTheftAlarmSystem.alarm.armStatus",
        name="Alarm Status",
        icon="mdi:shield-car",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMW CarData sensor entities."""
    coordinator: BMWCoordinator = hass.data[DOMAIN][entry.entry_id]
    vins: list[str] = entry.data[CONF_VINS]

    entities = [
        BMWSensorEntity(coordinator, vin, description)
        for vin in vins
        for description in SENSORS
    ]
    async_add_entities(entities)


class BMWSensorEntity(CoordinatorEntity[BMWCoordinator], SensorEntity):
    """A single BMW telemetry sensor."""

    entity_description: BMWSensorEntityDescription

    def __init__(
        self,
        coordinator: BMWCoordinator,
        vin: str,
        description: BMWSensorEntityDescription,
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
    def native_value(self) -> Any:
        """Return the current sensor value."""
        vin_data: dict[str, Any] = (self.coordinator.data or {}).get(self._vin, {})
        entry = vin_data.get(self.entity_description.descriptor)
        if entry is None:
            return None
        raw = entry.get("value")
        if raw is None:
            return None
        try:
            fn = self.entity_description.value_fn
            return fn(raw) if fn else raw
        except (ValueError, TypeError):
            return raw

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return unit and timestamp from BMW payload."""
        vin_data: dict[str, Any] = (self.coordinator.data or {}).get(self._vin, {})
        entry = vin_data.get(self.entity_description.descriptor, {})
        return {
            k: v for k, v in entry.items() if k != "value" and v is not None
        }
