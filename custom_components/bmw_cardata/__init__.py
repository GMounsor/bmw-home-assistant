"""BMW CarData Home Assistant integration."""
from __future__ import annotations

import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import BMWCarDataAPI
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

    # Refresh the container ID on startup so that a renamed CONTAINER_NAME
    # (descriptor-list version bump) triggers a new container automatically.
    #
    # We pass api.get_current_token() into the coordinator so both share the
    # same already-refreshed token — avoiding a second (invalid) refresh call.
    api = BMWCarDataAPI(session, data[CONF_CLIENT_ID], token)
    try:
        container_id = await api.get_or_create_container()
        token = api.get_current_token()
    except PermissionError:
        # Auth failure — fall through; coordinator will raise ConfigEntryAuthFailed
        container_id = data[CONF_CONTAINER_ID]
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not refresh container on startup, using stored ID: %s", err)
        container_id = data[CONF_CONTAINER_ID]

    if container_id != data.get(CONF_CONTAINER_ID):
        _LOGGER.info("Container ID updated: %s -> %s", data.get(CONF_CONTAINER_ID), container_id)
        hass.config_entries.async_update_entry(
            entry, data={**data, CONF_CONTAINER_ID: container_id}
        )

    coordinator = BMWCoordinator(
        hass=hass,
        session=session,
        client_id=data[CONF_CLIENT_ID],
        token=token,
        container_id=container_id,
        vins=data[CONF_VINS],
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await session.close()
        raise

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
