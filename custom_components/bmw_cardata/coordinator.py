"""DataUpdateCoordinator for BMW CarData."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
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
    TYRE_DIAGNOSIS_REFRESH_HOURS,
)

_LOGGER = logging.getLogger(__name__)


class BMWCoordinator(DataUpdateCoordinator):
    """Polls BMW CarData for all VINs on a schedule.

    coordinator.data is keyed by VIN. Each value is a dict with two keys:
        "telemetry"      - descriptor_id -> {value, unit, timestamp}
        "tyre_diagnosis" - raw response from the tyre diagnosis endpoint
                           (refreshed at most once every 23 hours)
    """

    def __init__(self, hass, session, client_id, token, container_id, vins):
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
        self._tyre_diagnosis_last_fetch = {}

    async def _async_update_data(self):
        """Fetch latest telemetry (and tyre diagnosis if due) for every VIN."""
        existing = self.data or {}
        result = {}

        try:
            for vin in self._vins:
                _LOGGER.debug("Fetching telematics for VIN %s", vin)
                telemetry = await self.api.get_telematics(vin, self._container_id)

                tyre_diagnosis = existing.get(vin, {}).get("tyre_diagnosis", {})
                last_fetch = self._tyre_diagnosis_last_fetch.get(vin)
                refresh_due = (
                    last_fetch is None
                    or (datetime.now() - last_fetch).total_seconds()
                    > TYRE_DIAGNOSIS_REFRESH_HOURS * 3600
                )
                if refresh_due:
                    _LOGGER.debug("Fetching tyre diagnosis for VIN %s", vin)
                    tyre_diagnosis = await self.api.get_tyre_diagnosis(vin)
                    self._tyre_diagnosis_last_fetch[vin] = datetime.now()

                result[vin] = {
                    "telemetry": telemetry,
                    "tyre_diagnosis": tyre_diagnosis,
                }

        except PermissionError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RuntimeError as err:
            raise UpdateFailed(str(err)) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching BMW data: {err}") from err

        self._persist_token()
        return result

    def _persist_token(self):
        """Write the current token back to the config entry if it was refreshed."""
        token = self.api.get_current_token()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_CLIENT_ID) == self._client_id:
                new_data = {
                    **entry.data,
                    CONF_ACCESS_TOKEN: token.access_token,
                    CONF_REFRESH_TOKEN: token.refresh_token,
                    CONF_TOKEN_EXPIRES_AT: token.expires_at,
                }
                self.hass.config_entries.async_update_entry(entry, data=new_data)
                break
