"""DataUpdateCoordinator for BMW CarData."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

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
    SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class BMWCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls BMW CarData for all VINs on a schedule.

    coordinator.data is keyed by VIN; each value is the raw telematicData dict
    returned by the API (descriptor_id → {value, unit, timestamp}).
    """

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        client_id: str,
        token: TokenData,
        container_id: str,
        vins: list[str],
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._session = session
        self._client_id = client_id
        self._container_id = container_id
        self._vins = vins
        self.api = BMWCarDataAPI(session, client_id, token)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch latest telemetry for every VIN."""
        result: dict[str, dict[str, Any]] = {}
        try:
            for vin in self._vins:
                _LOGGER.debug("Fetching telematics for VIN %s", vin)
                data = await self.api.get_telematics(vin, self._container_id)
                result[vin] = data
        except PermissionError as err:
            # Token revoked / re-auth required
            raise ConfigEntryAuthFailed(str(err)) from err
        except RuntimeError as err:
            # Rate limited
            raise UpdateFailed(str(err)) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching BMW data: {err}") from err

        # Persist any refreshed token back to the config entry
        self._persist_token()
        return result

    def _persist_token(self) -> None:
        """Write the current token to the config entry data (in case it was refreshed)."""
        token = self.api.get_current_token()
        # Find the config entry for this coordinator
        entries = self.hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            if entry.data.get(CONF_CLIENT_ID) == self._client_id:
                new_data = {
                    **entry.data,
                    CONF_ACCESS_TOKEN: token.access_token,
                    CONF_REFRESH_TOKEN: token.refresh_token,
                    CONF_TOKEN_EXPIRES_AT: token.expires_at,
                }
                self.hass.config_entries.async_update_entry(entry, data=new_data)
                break
