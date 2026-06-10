"""Device tracker platform for BMW CarData (GPS location)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VINS, DOMAIN
from .coordinator import BMWCoordinator

_LAT_DESCRIPTOR = "vehicle.cabin.infotainment.navigation.currentLocation.latitude"
_LON_DESCRIPTOR = "vehicle.cabin.infotainment.navigation.currentLocation.longitude"
_HEADING_DESCRIPTOR = "vehicle.cabin.infotainment.navigation.currentLocation.heading"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMW CarData device tracker entities."""
    coordinator: BMWCoordinator = hass.data[DOMAIN][entry.entry_id]
    vins: list[str] = entry.data[CONF_VINS]
    async_add_entities(BMWDeviceTracker(coordinator, vin) for vin in vins)


class BMWDeviceTracker(CoordinatorEntity[BMWCoordinator], TrackerEntity):
    """Tracks BMW GPS location."""

    def __init__(self, coordinator: BMWCoordinator, vin: str) -> None:
        super().__init__(coordinator)
        self._vin = vin
        self._attr_unique_id = f"{vin}_location"
        self._attr_name = f"BMW {vin[-4:]} Location"
        self._attr_icon = "mdi:car"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": f"BMW ({vin})",
            "manufacturer": "BMW",
        }

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS

    def _get_value(self, descriptor: str) -> float | None:
        telemetry = (self.coordinator.data or {}).get(self._vin, {}).get("telemetry", {})
        entry = telemetry.get(descriptor)
        if entry is None:
            return None
        raw = entry.get("value")
        try:
            return float(raw) if raw else None
        except (ValueError, TypeError):
            return None

    @property
    def latitude(self) -> float | None:
        return self._get_value(_LAT_DESCRIPTOR)

    @property
    def longitude(self) -> float | None:
        return self._get_value(_LON_DESCRIPTOR)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        heading = self._get_value(_HEADING_DESCRIPTOR)
        if heading is not None:
            return {"heading": heading}
        return {}
