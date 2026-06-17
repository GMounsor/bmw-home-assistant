"""DataUpdateCoordinator for BMW CarData."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import issue_registry as ir
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
    SCAN_INTERVAL_BY_VIN_COUNT,
    SCAN_INTERVAL_DEFAULT,
    TYRE_DIAGNOSIS_REFRESH_HOURS,
)

_LOGGER = logging.getLogger(__name__)

_REPAIRS_ISSUE_ID = "auth_failed"


class BMWCoordinator(DataUpdateCoordinator):
    """Polls BMW CarData for all VINs on a schedule.

    coordinator.data is keyed by VIN. Each value is a dict with two keys:
        "telemetry"      - descriptor_id -> {value, unit, timestamp}
        "tyre_diagnosis" - raw response from the tyre diagnosis endpoint
                           (refreshed at most once every 23 hours)
    """

    def __init__(self, hass, session, client_id, token, container_id, vins):
        interval = SCAN_INTERVAL_BY_VIN_COUNT.get(len(vins), SCAN_INTERVAL_DEFAULT)
        _LOGGER.debug("Poll interval: %d min for %d VIN(s)", interval, len(vins))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
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
                vin_result = await self._fetch_vin(vin, existing.get(vin, {}))
                result[vin] = vin_result

        except PermissionError as err:
            _LOGGER.error("BMW CarData authentication error (token refresh failed): %s", err)
            # Raise a HA repairs issue so the user gets a UI notification
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                _REPAIRS_ISSUE_ID,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="auth_failed",
            )
            raise ConfigEntryAuthFailed(str(err)) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error fetching BMW data: {err}") from err

        # Clear any existing auth issue on successful poll
        ir.async_delete_issue(self.hass, DOMAIN, _REPAIRS_ISSUE_ID)
        self._persist_token()
        return result

    async def _fetch_vin(self, vin: str, existing_vin_data: dict) -> dict:
        """Fetch telemetry + tyre diagnosis for a single VIN.

        If telemetry fails for this VIN, log a warning and return the last
        known data so other VINs and existing entity states are preserved.
        """
        try:
            _LOGGER.debug("Fetching telematics for VIN %s", vin)
            telemetry = await self.api.get_telematics(vin, self._container_id)
        except (RuntimeError, aiohttp.ClientError) as err:
            _LOGGER.warning(
                "Failed to fetch telemetry for VIN %s, keeping previous data: %s",
                vin,
                err,
            )
            telemetry = existing_vin_data.get("telemetry", {})

        tyre_diagnosis = existing_vin_data.get("tyre_diagnosis", {})
        last_fetch = self._tyre_diagnosis_last_fetch.get(vin)
        refresh_due = (
            last_fetch is None
            or (datetime.now() - last_fetch).total_seconds()
            > TYRE_DIAGNOSIS_REFRESH_HOURS * 3600
        )
        if refresh_due:
            try:
                _LOGGER.debug("Fetching tyre diagnosis for VIN %s", vin)
                tyre_diagnosis = await self.api.get_tyre_diagnosis(vin)
                self._tyre_diagnosis_last_fetch[vin] = datetime.now()
            except (RuntimeError, aiohttp.ClientError) as err:
                _LOGGER.warning(
                    "Failed to fetch tyre diagnosis for VIN %s, keeping previous data: %s",
                    vin,
                    err,
                )

        return {
            "telemetry": telemetry,
            "tyre_diagnosis": tyre_diagnosis,
        }

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
