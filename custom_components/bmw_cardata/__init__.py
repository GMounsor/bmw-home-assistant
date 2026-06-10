"""BMW CarData Home Assistant integration."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .auth import TokenData
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CONTAINER_ID,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    CONF_VINS,
    DOMAIN,
)
from .coordinator import BMWCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "device_tracker"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BMW CarData from a config entry."""
    data = entry.data

    token = TokenData(
        access_token=data[CONF_ACCESS_TOKEN],
        refresh_token=data[CONF_REFRESH_TOKEN],
        expires_at=data[CONF_TOKEN_EXPIRES_AT],
    )

    session = aiohttp.ClientSession()

    coordinator = BMWCoordinator(
        hass=hass,
        session=session,
        client_id=data[CONF_CLIENT_ID],
        token=token,
        container_id=data[CONF_CONTAINER_ID],
        vins=data[CONF_VINS],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: BMWCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator._session.close()
    return unload_ok
